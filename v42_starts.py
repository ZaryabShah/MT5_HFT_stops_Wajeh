"""v4.2 start-time robustness: same config, many different launch moments."""
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

V42 = dict(DEFAULT)
V42.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=None, regime_mult=4.0))

OFFSETS = [0, 60, 300, 900, 1800, 3600, 7200, 14400, 28800, 43200, 86400, 172800]

base = build_seconds()
fusion = respread(base, 0.031)

for name, secs, comm in [("Fusion (Monday's account)", fusion, 2.25),
                         ("Exness Standard", base, 0.0)]:
    cfg = dict(V42, commission_per_lot_side=comm)
    rng = minute_ranges(secs)
    t0 = int(secs["t"][0])
    nets = []
    print(f"\n=== {name} ===")
    print(f"{'start':>10} {'net':>10} {'maxDD':>10} {'cycles':>7} {'win%':>6}")
    for off in OFFSETS:
        idx = int(np.searchsorted(secs["t"], t0 + off))
        sub = {k: v[idx:] for k, v in secs.items()}
        r = run(cfg, sub, rng)
        nets.append(r["net"])
        tag = f"+{off}s" if off < 3600 else f"+{off // 3600}h"
        print(f"{tag:>10} {r['net']:>+10.2f} {r['max_dd']:>+10.2f} "
              f"{r['n']:>7} {r['win_rate'] * 100:>5.0f}%")
    nets = np.array(nets)
    print(f"  -> all {len(nets)} runs: min {nets.min():+.2f} / "
          f"mean {nets.mean():+.2f} / max {nets.max():+.2f} | "
          f"positive {100 * (nets > 0).mean():.0f}% of starts")
