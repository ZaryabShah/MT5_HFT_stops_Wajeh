"""Start-time robustness for step_cap=2.50 + daily_stop=50 (4 months)."""
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

cfg = dict(DEFAULT)
cfg.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=2.5, regime_mult=4.0,
                commission_per_lot_side=2.25, daily_stop=50))

secs = respread(build_seconds(), 0.031)
rng = minute_ranges(secs)
t0 = int(secs["t"][0])
for off in (0, 900, 3600, 14400, 86400):
    idx = int(np.searchsorted(secs["t"], t0 + off))
    sub = {k: v[idx:] for k, v in secs.items()}
    r = run(cfg, sub, rng)
    print(f"start +{off:>6}s: net {r['net']:+9.2f} | maxDD {r['max_dd']:+9.2f} | "
          f"{r['n']} cycles | {r['win_rate']*100:.0f}% wins")
