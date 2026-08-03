"""Start-time robustness for the two winning trend gates."""
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from trend_gate import er_series, move_series, secs, rng

V46 = dict(DEFAULT)
V46.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50,
                hours={22, 23, 0, 1, 2, 3, 4, 5}))

t0 = int(secs["t"][0])
for label, series in [("ER(30m)>=0.25", er_series(30, 0.25)),
                      ("|move30m|>=$3", move_series(30, 3.0))]:
    print(f"\n=== {label} ===")
    for off in (0, 900, 3600, 14400, 86400):
        idx = int(np.searchsorted(secs["t"], t0 + off))
        sub = {k: v[idx:] for k, v in secs.items()}
        r = run(dict(V46, gate_series=series[idx:]), sub, rng)
        print(f"start +{off:>6}s: net {r['net']:+9.2f} | maxDD {r['max_dd']:+9.2f} | "
              f"{r['n']} cyc | {r['win_rate']*100:.0f}%")
