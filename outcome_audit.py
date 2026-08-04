"""How did each v4.8 cycle actually END? Proof the backtest P/L comes from
the spec'd exits (target / trail / last-stop close / protective stops)."""
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
print(f"total: net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cycles\n")
print(f"{'outcome':<12}{'count':>6}{'total pnl':>12}{'avg pnl':>10}{'wins':>6}")
for oc in ("target", "trail", "all_filled", "equitystop", "paircap"):
    sub = [c for c in r["cycles"] if c["outcome"] == oc]
    if not sub:
        continue
    tot = sum(c["pnl"] for c in sub)
    w = sum(1 for c in sub if c["pnl"] > 0)
    print(f"{oc:<12}{len(sub):>6}{tot:>+12.2f}{tot / len(sub):>+10.2f}{w:>6}")
