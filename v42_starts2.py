"""Start Mon Jul 20 with $1,000: daily ledgers for BOTH v5-restart (0.45)
and v4.6, on the real Fusion feed."""
from datetime import datetime, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0
STEP = 0.45

full = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
start = int(datetime(2026, 7, 20, 0, 0, tzinfo=timezone.utc).timestamp())
idx = int(np.searchsorted(full["t"], start))
secs = {k: v[idx:] for k, v in full.items()}
t = secs["t"]

# ---------- v5-restart daily ----------
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

print("=== v5-restart 0.45, started Mon Jul 20, $1,000 ===")
print(f"{'day':<11}{'wins':>5}{'deaths':>7}{'lowest eq':>11}{'end eq':>9}{'net':>10}")
for dkey, d in days.items():
    print(f"{dkey:<11}{d['wins']:>5}{d['deaths']:>7}{d['min_eq']:>11.2f}"
          f"{d['end_eq']:>9.2f}{d['end_eq'] - BANK0 * deposits:>+10.2f}")
final_eq = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                   if anchor_a is not None else 0.0)
print(f"deposits {deposits} | final eq {final_eq:.2f} | NET {final_eq - deposits * BANK0:+.2f}")
for ts, dur in deaths_log:
    print(f"  DEATH {datetime.fromtimestamp(ts, tz=timezone.utc):%a %m-%d %H:%M} "
          f"(life {dur:.2f}d)")

# ---------- v4.6 daily ----------
V46 = dict(DEFAULT)
V46.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50,
                hours={22, 23, 0, 1, 2, 3, 4, 5}))
rng = minute_ranges(full)
r = run(V46, secs, rng)
print("\n=== v4.6, started Mon Jul 20, $1,000 ===")
days2 = {}
bal = 1000.0
for c in r["cycles"]:
    bal += c["pnl"]
    dkey = datetime.fromtimestamp(c["t"], tz=timezone.utc).strftime("%a %m-%d")
    days2.setdefault(dkey, []).append((bal, c["pnl"]))
print(f"{'day':<11}{'cyc':>4}{'W-L':>7}{'end bal':>9}{'lowest':>9}{'day net':>9}")
prev = 1000.0
for dkey, rows in days2.items():
    end = rows[-1][0]
    lowest = min(prev, min(b for b, _ in rows))
    net = sum(p for _, p in rows)
    wins = sum(1 for _, p in rows if p > 0)
    print(f"{dkey:<11}{len(rows):>4}{f'{wins}-{len(rows)-wins}':>7}{end:>9.2f}"
          f"{lowest:>9.2f}{net:>+9.2f}")
    prev = end
print(f"final {prev:.2f} | NET {prev - 1000:+.2f}")
