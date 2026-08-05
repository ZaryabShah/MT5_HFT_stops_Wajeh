"""Calculated-aggression ladder: the staged v4.8 build (gap5) cycle sequence,
tiered compounding at rising risk densities, stress-tested from every
starting week. Density = dollars of balance per 0.01 lots (1000 = validated
rule; 333 = 3x aggression). Death/ruin proxy: balance <= $250 per 0.01-lot
density unit (margin + spread room gone)."""
from datetime import datetime, timedelta, timezone

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))
res = run(V48, secs, rng)          # respawn_gap=5 via new DEFAULT
cyc = res["cycles"]
print(f"engine: net {res['net']:+.2f} | maxDD {res['max_dd']:+.2f} | "
      f"{res['n']} cycles (staged build, 0.01 lots)\n")

weeks = sorted({(datetime.fromtimestamp(int(c['t']), tz=timezone.utc)
                 - timedelta(days=datetime.fromtimestamp(
                     int(c['t']), tz=timezone.utc).weekday())).strftime("%m-%d")
                for c in cyc})


def sim(cycles, density, start=1000.0):
    """Tiered compounding: lot re-set daily = floor(balance/density)*0.01."""
    bal, lot, day = start, 0.01, None
    lo, peak, mdd = start, start, 0.0
    for c in cycles:
        d = c["t"] // 86400
        if d != day:
            day = d
            lot = max(0.01, int(bal // density) * 0.01)
        bal += c["pnl"] * lot / 0.01
        lo = min(lo, bal)
        peak = max(peak, bal)
        mdd = min(mdd, bal / peak - 1)
        if bal <= 250 * (density / 1000):
            return bal, lo, mdd, True
    return bal, lo, mdd, False


print(f"{'density':<22}{'final($1k,full 4mo)':>20}{'min bal':>9}{'maxDD%':>8}"
      f"{'ruins/18 starts':>16}{'median final':>13}")
for density, label in ((1000, "1.0x (validated)"), (667, "1.5x"),
                       (500, "2.0x"), (333, "3.0x")):
    fin, lo, mdd, dead = sim(cyc, density)
    finals, ruins = [], 0
    for wk in weeks:                      # start the journey at each week
        sub = [c for c in cyc
               if (datetime.fromtimestamp(int(c['t']), tz=timezone.utc)
                   - timedelta(days=datetime.fromtimestamp(
                       int(c['t']), tz=timezone.utc).weekday())
                   ).strftime("%m-%d") >= wk]
        f2, _, _, d2 = sim(sub, density)
        finals.append(f2)
        ruins += d2
    finals.sort()
    med = finals[len(finals) // 2]
    print(f"{label:<22}{fin:>20.2f}{lo:>9.2f}{mdd * 100:>7.1f}%"
          f"{ruins:>16}{med:>13.2f}", flush=True)
print("\nDONE aggression_ladder")
