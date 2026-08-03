"""IS/OOS split test for the W1 window (20-22 U 00-06) vs baseline 22-06.
Halves: Apr 2 - May 31 vs Jun 1 - Jul 31. A real edge should win BOTH halves."""
from datetime import datetime, timezone

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)

V47 = dict(DEFAULT)
V47.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={22, 23, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))
W1 = {20, 21, 0, 1, 2, 3, 4, 5}
MID = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())

print(f"{'variant':<26}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}")
for half, tf, tt in [("Apr-May", None, MID), ("Jun-Jul", MID, None)]:
    for label, hrs in [("BASE 22-06", V47["hours"]), ("W1 20-22U00-06", W1)]:
        r = run(dict(V47, hours=hrs), secs, rng, t_from=tf, t_to=tt)
        print(f"{half} {label:<18}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}"
              f"{r['n']:>6}{r['win_rate'] * 100:>5.0f}%", flush=True)
print("\nDONE research_split")
