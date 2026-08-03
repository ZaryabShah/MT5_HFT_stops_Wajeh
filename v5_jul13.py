"""Start Mon Jul 13 ($1,000): v5-restart at 0.30 and 0.45 gaps, plus v4.6."""
from datetime import datetime, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0

full = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
START = datetime(2026, 7, 13, tzinfo=timezone.utc)
idx = int(np.searchsorted(full["t"], int(START.timestamp())))
secs = {k: v[idx:] for k, v in full.items()}
t = secs["t"]


def ledger(step):
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
        while ah >= anchor_a + nb * step:
            longs.append(max(anchor_a + nb * step, ao))
            bank -= COMM_HALF
            nb += 1
        while bl <= anchor_b - ns * step:
            shorts.append(min(anchor_b - ns * step, bo))
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
    final_eq = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                       if anchor_a is not None else 0.0)
    print(f"\n=== v5-restart gap {step}, from Mon Jul 13 ===")
    print(f"{'day':<11}{'wins':>5}{'deaths':>7}{'lowest eq':>11}{'end eq':>9}{'net':>10}")
    for dkey, d in days.items():
        print(f"{dkey:<11}{d['wins']:>5}{d['deaths']:>7}{d['min_eq']:>11.2f}"
              f"{d['end_eq']:>9.2f}{d['end_eq'] - BANK0 * deposits:>+10.2f}")
    print(f"deposits {deposits} | final eq {final_eq:.2f} | "
          f"NET {final_eq - deposits * BANK0:+.2f}")
    for ts, dur in deaths_log:
        print(f"  DEATH {datetime.fromtimestamp(ts, tz=timezone.utc):%a %m-%d %H:%M} "
              f"(life {dur:.2f}d)")


ledger(0.30)
ledger(0.45)

V46 = dict(DEFAULT)
V46.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50,
                hours={22, 23, 0, 1, 2, 3, 4, 5}))
r = run(V46, secs, minute_ranges(full))
bal = 1000.0
weekly = {}
for c in r["cycles"]:
    bal += c["pnl"]
    wk = datetime.fromtimestamp(c["t"], tz=timezone.utc).strftime("%m-%d")
print(f"\n=== v4.6 from Mon Jul 13: net {r['net']:+.2f}, final {bal:.2f}, "
      f"maxDD {r['max_dd']:+.2f}, {r['n']} cycles ===")
