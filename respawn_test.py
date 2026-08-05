"""Does the 30s respawn gap (RESTART_DELAY_SEC / respawn_gap) matter?
v4.8 stack, 4-month real feed, gap = 0/5/15/30/60/120s."""
from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))

print(f"{'respawn gap':<14}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}")
for g in (0, 5, 15, 30, 60, 120):
    r = run(dict(V48, respawn_gap=g), secs, rng)
    tag = " (current)" if g == 30 else ""
    print(f"{str(g) + 's' + tag:<14}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}"
          f"{r['n']:>6}{r['win_rate'] * 100:>5.0f}%", flush=True)
print("\nDONE respawn_test")
