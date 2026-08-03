"""Robustness + weekly table for the 22-06 UTC overnight window (v4.6 cand)."""
from datetime import datetime, timedelta, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

HRS = {22, 23, 0, 1, 2, 3, 4, 5}
V46 = dict(DEFAULT)
V46.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50, hours=HRS))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)
t0 = int(secs["t"][0])

print("=== robustness: 22-06 window, 5 start times ===")
for off in (0, 900, 3600, 14400, 86400):
    idx = int(np.searchsorted(secs["t"], t0 + off))
    sub = {k: v[idx:] for k, v in secs.items()}
    r = run(V46, sub, rng)
    print(f"start +{off:>6}s: net {r['net']:+9.2f} | maxDD {r['max_dd']:+9.2f} | "
          f"{r['n']} cyc | {r['win_rate']*100:.0f}%")

print("\n=== weekly: 22-06 window (from $1,000) ===")
r = run(V46, secs, rng)
weeks = {}
bal = 1000.0
for c in r["cycles"]:
    bal += c["pnl"]
    d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
    monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
    weeks.setdefault(monday, []).append((bal, c["pnl"]))
print(f"{'week':<8}{'start':>9}{'end':>9}{'lowest':>9}{'net':>9}")
prev = 1000.0
for wk in sorted(weeks):
    rows = weeks[wk]
    end = rows[-1][0]
    lowest = min(prev, min(b for b, _ in rows))
    net = sum(p for _, p in rows)
    print(f"{wk:<8}{prev:>9.2f}{end:>9.2f}{lowest:>9.2f}{net:>+9.2f}")
    prev = end
