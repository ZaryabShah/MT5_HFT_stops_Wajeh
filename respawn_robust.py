"""Robustness of respawn_gap=5 before adoption: 5 start offsets, IS/OOS
halves, and combination with recheck_sec=2 (the live cadence)."""
from datetime import datetime, timezone

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))
t0 = int(secs["t"][0])
MID = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())

print("=== 5 start offsets (gap=5 vs gap=30) ===")
for label, g in (("gap 5s ", 5), ("gap 30s", 30)):
    nets, dds = [], []
    for off in (0, 3600, 10800, 25200, 46800):
        r = run(dict(V48, respawn_gap=g), secs, rng, t_from=t0 + off)
        nets.append(r["net"])
        dds.append(r["max_dd"])
    print(f"{label} nets: " + " ".join(f"{x:>+9.2f}" for x in nets)
          + f" | worst DD {min(dds):+.2f}", flush=True)

print("\n=== IS/OOS halves ===")
for half, tf, tt in (("Apr-May", None, MID), ("Jun-Jul", MID, None)):
    for label, g in (("gap 5s ", 5), ("gap 30s", 30)):
        r = run(dict(V48, respawn_gap=g), secs, rng, t_from=tf, t_to=tt)
        print(f"{half} {label}: net {r['net']:>+9.2f} | maxDD {r['max_dd']:>+8.2f} "
              f"| {r['n']} cyc", flush=True)

print("\n=== combined with live cadence recheck=2s ===")
r = run(dict(V48, respawn_gap=5, recheck_sec=2), secs, rng)
print(f"gap 5s + recheck 2s: net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} "
      f"| {r['n']} cyc")
print("\nDONE respawn_robust")
