"""Hour-window sweep, part A: SMALL CHUNKS (2h and 4h windows), all with the
v4.7 trend gate + $50 breaker. Real Fusion feed, 4 months, 0.01 lots.
Windows gate cycle STARTS only; open cycles always finish naturally."""
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


WINDOWS = []
for a in range(0, 24, 2):                        # 2h chunks
    WINDOWS.append((f"{a:02d}-{(a + 2) % 24:02d} (2h)", wrap(a, a + 2)))
for a in range(0, 24, 4):                        # 4h chunks
    WINDOWS.append((f"{a:02d}-{(a + 4) % 24:02d} (4h)", wrap(a, a + 4)))
for a in range(2, 24, 4):                        # 4h chunks, offset 2
    WINDOWS.append((f"{a:02d}-{(a + 4) % 24:02d} (4h)", wrap(a, a + 4)))

print(f"{'window':<16}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}{'net/DD':>7}")
for label, hrs in WINDOWS:
    r = run(dict(BASE, hours=hrs), secs, rng)
    nd = r["net"] / -r["max_dd"] if r["max_dd"] < 0 else float("inf")
    print(f"{label:<16}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate'] * 100:>5.0f}%{nd:>7.1f}", flush=True)
print("\nDONE research_hours_a")
