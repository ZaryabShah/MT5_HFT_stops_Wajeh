"""Hour-window sweep, part B: whole day, sessions, 6h/8h/10h/12h windows —
all with the v4.7 trend gate + $50 breaker. Real Fusion feed, 4 months."""
from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                 step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                 daily_stop=50, gate_series=GATE))


def wrap(a, b):
    return set(h % 24 for h in range(a, b if b > a else b + 24))


WINDOWS = [
    ("24h WHOLE DAY", None),
    ("22-06 v4.7 base", wrap(22, 6)),
    # 6h
    ("00-06 (6h)", wrap(0, 6)), ("06-12 (6h)", wrap(6, 12)),
    ("12-18 (6h)", wrap(12, 18)), ("18-24 (6h)", wrap(18, 24)),
    ("21-03 (6h)", wrap(21, 3)), ("22-04 (6h)", wrap(22, 4)),
    ("23-05 (6h)", wrap(23, 5)),
    # 8h
    ("00-08 (8h)", wrap(0, 8)), ("08-16 (8h)", wrap(8, 16)),
    ("16-24 (8h)", wrap(16, 24)), ("20-04 (8h)", wrap(20, 4)),
    ("14-22 (8h)", wrap(14, 22)),
    # 10h around the baseline
    ("20-06 (10h)", wrap(20, 6)), ("21-07 (10h)", wrap(21, 7)),
    ("22-08 (10h)", wrap(22, 8)),
    # 12h halves
    ("18-06 (12h)", wrap(18, 6)), ("06-18 (12h)", wrap(6, 18)),
    ("22-10 (12h)", wrap(22, 10)), ("10-22 (12h)", wrap(10, 22)),
]

print(f"{'window':<18}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}{'net/DD':>7}")
for label, hrs in WINDOWS:
    r = run(dict(BASE, hours=hrs), secs, rng)
    nd = r["net"] / -r["max_dd"] if r["max_dd"] < 0 else float("inf")
    print(f"{label:<18}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate'] * 100:>5.0f}%{nd:>7.1f}", flush=True)
print("\nDONE research_hours_b")
