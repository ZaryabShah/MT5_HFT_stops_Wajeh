"""Weekly ledger for v4.8 (composite window) @ 0.01 lots from $1,000.
Real Fusion feed, Apr 2 - Jul 31. Weeks labeled by their Monday (server time)."""
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
r = run(V48, secs, rng)

START = 1000.0
bal = START
lowest_ever = START
weeks = {}          # monday-label -> dict
order = []
for c in r["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=timezone.utc)
    wk = (d - timedelta(days=d.weekday())).strftime("%m-%d")
    if wk not in weeks:
        weeks[wk] = dict(start=bal, cyc=0, w=0, l=0, low=bal, peak=bal, dd=0.0)
        order.append(wk)
    bal += c["pnl"]
    lowest_ever = min(lowest_ever, bal)
    wkd = weeks[wk]
    wkd["cyc"] += 1
    wkd["w" if c["pnl"] > 0 else "l"] += 1
    wkd["low"] = min(wkd["low"], bal)
    wkd["peak"] = max(wkd["peak"], bal)
    wkd["dd"] = min(wkd["dd"], bal - wkd["peak"])
    wkd["end"] = bal

wins = sum(w["w"] for w in weeks.values())
print(f"===== v4.8 @ 0.01 lots, breaker $50, start $1000 =====")
print(f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cyc | "
      f"{100 * wins / r['n']:.0f}% wins | final {bal:.2f} | "
      f"lowest ever {lowest_ever:.2f}\n")
print(f"{'week':<7}{'cyc':>4}{'W-L':>7}{'start':>10}{'end':>10}{'lowest':>10}"
      f"{'net':>10}{'wk DD':>9}")
for wk in order:
    d = weeks[wk]
    print(f"{wk:<7}{d['cyc']:>4}{str(d['w']) + '-' + str(d['l']):>7}"
          f"{d['start']:>10.2f}{d['end']:>10.2f}{d['low']:>10.2f}"
          f"{d['end'] - d['start']:>+10.2f}{d['dd']:>9.2f}")
