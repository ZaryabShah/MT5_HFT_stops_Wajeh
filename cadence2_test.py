"""Full 4-month v4.8 with recheck_sec=2 — the exact new live cadence."""
from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))
r = run(dict(V48, recheck_sec=2), secs, rng)
print(f"recheck 2s: net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | "
      f"{r['n']} cyc | {r['win_rate'] * 100:.0f}% wins")
