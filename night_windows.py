"""Follow-up: the Western sessions LOSE standalone — test blocking them
entirely (overnight-only variants) on the real feed."""
from backtest import DEFAULT, build_seconds, minute_ranges, run

V45 = dict(DEFAULT)
V45.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)

for label, hrs in [
    ("20-07 (block Ldn+US)", {20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6}),
    ("21-06", {21, 22, 23, 0, 1, 2, 3, 4, 5}),
    ("22-06", {22, 23, 0, 1, 2, 3, 4, 5}),
    ("00-06", {0, 1, 2, 3, 4, 5}),
]:
    r = run(dict(V45, hours=hrs), secs, rng)
    print(f"{label:<22}: net {r['net']:>+9.2f} | maxDD {r['max_dd']:>+9.2f} | "
          f"{r['n']:>4} cyc | {r['win_rate']*100:.0f}% | "
          f"net/DD {abs(r['net']/r['max_dd']):.2f}")
