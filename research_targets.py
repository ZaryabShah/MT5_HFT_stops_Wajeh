"""Target-size & SL-ratio sweep on full v4.7 (trend gate + 22-06 + $50 breaker).
Real Fusion feed, 4 months. Fixed 0.01 lots.

Target size is varied via target_level n: target $ = lot*100*step*n(n-1)/2.
Equivalent 'percent of the L11 basis' printed for each n.
"""
from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)

V47 = dict(DEFAULT)
V47.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={22, 23, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))


def show(label, r):
    nd = r["net"] / -r["max_dd"] if r["max_dd"] < 0 else float("inf")
    print(f"{label:<38}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate'] * 100:>5.0f}%{nd:>7.1f}", flush=True)


print("=== A. target size, SL scales with target (sl/target ratio 2:3) ===")
print(f"{'variant':<38}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}{'net/DD':>7}")
for n in (6, 7, 8, 9, 10, 11, 13):
    eq = 0.12 * n * (n - 1) / 110          # % of the L11 basis
    show(f"target@L{n:<2} (~{eq * 100:4.1f}% of L11 basis)",
         run(dict(V47, target_level=n), secs, rng))

print("\n=== B. target size, SL dollars HELD at the L11 scale ===")
for n in (7, 8, 9, 10, 11, 13):
    slp = 0.08 * 110 / (n * (n - 1))
    show(f"target@L{n:<2}, SL fixed (sl_pct {slp:.3f})",
         run(dict(V47, target_level=n, sl_pct=slp), secs, rng))

print("\n=== C. SL ratio at the L11 target ===")
for slp in (0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.16):
    show(f"sl_pct {slp:.2f} (SL = {slp / 0.12:.2f}x target)",
         run(dict(V47, sl_pct=slp), secs, rng))
print("\nDONE research_targets")
