"""Weekly balance table for the density ladder (tiered daily compounding,
staged v4.8 build, $1,000 start Apr 2)."""
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
cyc = run(V48, secs, rng)["cycles"]

DENS = [(1000, "1.0x"), (667, "1.5x"), (500, "2.0x"), (333, "3.0x")]
paths = {}
for dens, label in DENS:
    bal, lot, day = 1000.0, 0.01, None
    weekly = {}
    lots = {}
    for c in cyc:
        d = c["t"] // 86400
        if d != day:
            day = d
            lot = max(0.01, int(bal // dens) * 0.01)
        bal += c["pnl"] * lot / 0.01
        dt = datetime.fromtimestamp(int(c["t"]), tz=timezone.utc)
        wk = (dt - timedelta(days=dt.weekday())).strftime("%m-%d")
        weekly[wk] = bal
        lots[wk] = lot
    paths[label] = (weekly, lots)

weeks = sorted(paths["1.0x"][0])
print(f"{'week':<7}" + "".join(f"{lb + ' end':>12}{'lot':>6}" for _, lb in DENS))
for wk in weeks:
    row = f"{wk:<7}"
    for _, lb in DENS:
        w, l = paths[lb]
        row += f"{w[wk]:>12.2f}{l[wk]:>6.2f}"
    print(row, flush=True)
print("\nDONE ladder_weekly")
