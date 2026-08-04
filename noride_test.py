"""Spec-deviation test: v4.8 WITHOUT the last-stop close — after the final
grid level fills, keep riding until target / trail / equity stop.
Everything else identical. Full report + outcome audit + weekly ledger."""
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

r = run(dict(V48, last_stop_close=False), secs, rng)
print(f"===== v4.8 variant: NO last-stop close (ride past grid) =====")
print(f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cyc | "
      f"win% {r['win_rate'] * 100:.0f}%")
print(f"(baseline v4.8 with last-stop close: net +3872.26 | maxDD -503.53 | "
      f"607 cyc | 54%)\n")

print(f"{'outcome':<12}{'count':>6}{'total pnl':>12}{'avg pnl':>10}{'wins':>6}")
for oc in ("target", "trail", "all_filled", "equitystop", "paircap"):
    sub = [c for c in r["cycles"] if c["outcome"] == oc]
    if not sub:
        continue
    tot = sum(c["pnl"] for c in sub)
    w = sum(1 for c in sub if c["pnl"] > 0)
    print(f"{oc:<12}{len(sub):>6}{tot:>+12.2f}{tot / len(sub):>+10.2f}{w:>6}")

START = 1000.0
bal = START
lowest_ever = START
weeks, order = {}, []
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

print(f"\nfinal {bal:.2f} | lowest ever {lowest_ever:.2f}")
print(f"{'week':<7}{'cyc':>4}{'W-L':>7}{'start':>10}{'end':>10}{'lowest':>10}"
      f"{'net':>10}{'wk DD':>9}")
for wk in order:
    d = weeks[wk]
    print(f"{wk:<7}{d['cyc']:>4}{str(d['w']) + '-' + str(d['l']):>7}"
          f"{d['start']:>10.2f}{d['end']:>10.2f}{d['low']:>10.2f}"
          f"{d['end'] - d['start']:>+10.2f}{d['dd']:>9.2f}")
