"""The decisive test: parameter re-tune on the REAL Fusion feed (48 configs,
both trigger modes, breaker $50 as exploration floor) + the finalized config
on the REAL Exness feed (fixed $0.24 spread = no phantom fills possible)."""
import itertools

from backtest import DEFAULT, build_seconds, minute_ranges, run

BASE = dict(DEFAULT)
BASE.update(dict(purge_at=5, trail_arm=0.5, regime_mult=4.0, daily_stop=50))

print("=== A) REAL FUSION FEED: 48-config re-tune (comm $2.25/side) ===")
fus = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
frng = minute_ranges(fus)
rows = []
for trig, sl, gb, cap, gate in itertools.product(
        (False, True), (0.06, 0.08), (0.3, 0.4), (1.5, 2.5, None), (4.0, 6.0)):
    cfg = dict(BASE, trigger_on_mid=trig, sl_pct=sl, trail_giveback=gb,
               step_cap=cap, regime_mult=gate, commission_per_lot_side=2.25)
    r = run(cfg, fus, frng)
    rows.append((r["net"], r["max_dd"], r["n"], trig, sl, gb, cap, gate))
rows.sort(key=lambda x: -x[0])
print(f"{'net':>9} {'maxDD':>9} {'cyc':>5}  trig  sl   gvbk cap   gate")
for r in rows[:10]:
    print(f"{r[0]:>+9.2f} {r[1]:>+9.2f} {r[2]:>5}  {'MID' if r[3] else 'quo'}  "
          f"{r[4]:.2f} {r[5]:.1f}  {str(r[6]):<5} {r[7]:.0f}")
pos = sum(1 for r in rows if r[0] > 0)
print(f"positive configs: {pos}/{len(rows)}")

print("\n=== B) REAL EXNESS FEED (fixed $0.24 spread, no commission) ===")
exn = build_seconds()          # data/ticks.npz (4 months, real Exness)
erng = minute_ranges(exn)
for L in (None, 50):
    for gate in (4.0, 6.0):
        cfg = dict(BASE, sl_pct=0.06, trail_giveback=0.4, step_cap=2.5,
                   regime_mult=gate, daily_stop=L, commission_per_lot_side=0.0)
        r = run(cfg, exn, erng)
        print(f"breaker {str(L):>4}, gate {gate:.0f}x: net {r['net']:>+9.2f} | "
              f"maxDD {r['max_dd']:>+9.2f} | {r['n']} cyc | "
              f"{r['win_rate']*100:.0f}% wins")
