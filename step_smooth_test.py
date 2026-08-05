"""User idea: change grid spacing SLOWLY (over 2-3 cycles) instead of fresh
each cycle. Variants: EMA-blended step (2-cycle / 3-cycle memory) and
confirm-based (switch only after 2-3 consecutive >30% deviations)."""
from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))

print(f"{'variant':<30}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}")
CELLS = [
    ("instant re-step (current)", {}),
    ("EMA 2-cycle (a=0.5)", dict(step_ema=0.5)),
    ("EMA 3-cycle (a=0.33)", dict(step_ema=0.33)),
    ("confirm 2x >30% dev", dict(step_confirm=(2, 0.3))),
    ("confirm 3x >30% dev", dict(step_confirm=(3, 0.3))),
]
for label, extra in CELLS:
    r = run(dict(V48, **extra), secs, rng)
    print(f"{label:<30}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate'] * 100:>5.0f}%", flush=True)
print("\nDONE step_smooth_test")
