"""v5-restart (0.45 spacing, no sweep): start $1,000 on Monday Jul 27,
run to the Friday Jul 31 close. Day-by-day ledger with death events."""
from datetime import datetime, timezone

import numpy as np

from backtest import build_seconds

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0
STEP = 0.45

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
start = int(datetime(2026, 7, 27, 0, 0, tzinfo=timezone.utc).timestamp())
idx = int(np.searchsorted(secs["t"], start))
secs = {k: v[idx:] for k, v in secs.items()}
t = secs["t"]
print(f"start: {datetime.fromtimestamp(int(t[0]), tz=timezone.utc):%a %m-%d %H:%M} "
      f"(server time) | end: {datetime.fromtimestamp(int(t[-1]), tz=timezone.utc):%a %m-%d %H:%M}")

bank = BANK0
deposits = 1
days = {}
deaths_log = []
longs, shorts = [], []
nb = ns = 1
anchor_a = anchor_b = None
idle_until = 0
life_start = int(t[0])
j = 0
n = len(t)
while j < n:
    dkey = datetime.fromtimestamp(int(t[j]), tz=timezone.utc).strftime("%a %m-%d")
    d = days.setdefault(dkey, dict(wins=0, deaths=0, min_eq=1e18, end_eq=bank))
    if anchor_a is None:
        if t[j] >= idle_until:
            anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
            longs, shorts = [], []
            nb = ns = 1
        j += 1
        continue
    ah, bl = secs["ask_h"][j], secs["bid_l"][j]
    ao, bo = secs["ask_o"][j], secs["bid_o"][j]
    bc, ac = secs["bid_c"][j], secs["ask_c"][j]
    while ah >= anchor_a + nb * STEP:
        longs.append(max(anchor_a + nb * STEP, ao))
        bank -= COMM_HALF
        nb += 1
    while bl <= anchor_b - ns * STEP:
        shorts.append(min(anchor_b - ns * STEP, bo))
        bank -= COMM_HALF
        ns += 1
    profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts)
    eq = bank + profit
    d["min_eq"] = min(d["min_eq"], eq)
    d["end_eq"] = eq
    if profit >= TARGET:
        bank += profit - COMM_HALF * (len(longs) + len(shorts))
        d["wins"] += 1
        anchor_a = None
        idle_until = t[j] + 30
    elif eq <= DEATH:
        deaths_log.append((int(t[j]), (t[j] - life_start) / 86400))
        d["deaths"] += 1
        bank = BANK0
        deposits += 1
        life_start = int(t[j])
        anchor_a = None
        idle_until = t[j] + 30
    j += 1

print(f"\n{'day':<11}{'wins':>5}{'deaths':>7}{'lowest eq':>11}{'day-end eq':>12}"
      f"{'net-to-date':>13}")
run_net = 0.0
for dkey, d in days.items():
    net_td = d["end_eq"] - deposits * BANK0 + (deposits - 1) * 0  # eq - all deposits
    print(f"{dkey:<11}{d['wins']:>5}{d['deaths']:>7}{d['min_eq']:>11.2f}"
          f"{d['end_eq']:>12.2f}{d['end_eq'] - BANK0 * deposits:>+13.2f}")
final_eq = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                   if anchor_a is not None else 0.0)
print(f"\ndeposits: {deposits} x $1,000 | final equity {final_eq:.2f} | "
      f"NET {final_eq - deposits * BANK0:+.2f}")
for ts, dur in deaths_log:
    print(f"  DEATH {datetime.fromtimestamp(ts, tz=timezone.utc):%a %m-%d %H:%M} "
          f"— life lasted {dur:.2f} days -> restarted with fresh $1,000")
if not deaths_log:
    print("  no deaths — the first $1,000 survived the whole week")
