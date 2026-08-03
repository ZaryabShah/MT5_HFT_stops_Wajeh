"""v4.7 weekly tables at 0.02 and 0.03 lots (breaker scaled to $100/$150,
starting balance scaled to $2,000/$3,000 per the $1k-per-0.01-lot rule)."""
from datetime import datetime, timedelta, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run
from trend_gate import er_series, move_series

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)
gate = er_series(30, 0.25) & move_series(30, 3.0)

for lot, stop, start_bal in ((0.02, 100, 2000.0), (0.03, 150, 3000.0)):
    cfg = dict(DEFAULT)
    cfg.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                    purge_at=5, step_cap=2.5, regime_mult=6.0,
                    commission_per_lot_side=2.25, daily_stop=stop,
                    hours={22, 23, 0, 1, 2, 3, 4, 5}, gate_series=gate,
                    lot=lot))
    r = run(cfg, secs, rng)
    weeks = {}
    bal = start_bal
    low_ever = start_bal
    for c in r["cycles"]:
        bal += c["pnl"]
        low_ever = min(low_ever, bal)
        d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
        monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
        weeks.setdefault(monday, []).append((bal, c["pnl"]))
    print(f"\n===== v4.7 @ {lot} lots, breaker ${stop}, start ${start_bal:.0f} =====")
    print(f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cyc | "
          f"{r['win_rate']*100:.0f}% wins | final {start_bal + r['net']:.2f} | "
          f"lowest ever {low_ever:.2f}")
    print(f"{'week':<7}{'cyc':>4}{'W-L':>7}{'start':>10}{'end':>10}{'lowest':>10}"
          f"{'net':>10}{'wk DD':>9}")
    prev = start_bal
    for wk in sorted(weeks):
        rows = weeks[wk]
        bals = [b for b, _ in rows]
        end = bals[-1]
        lowest = min(prev, min(bals))
        net = sum(p for _, p in rows)
        wins = sum(1 for _, p in rows if p > 0)
        peak = prev
        dd = 0.0
        for b in bals:
            peak = max(peak, b)
            dd = min(dd, b - peak)
        print(f"{wk:<7}{len(rows):>4}{f'{wins}-{len(rows)-wins}':>7}{prev:>10.2f}"
              f"{end:>10.2f}{lowest:>10.2f}{net:>+10.2f}{dd:>+9.2f}")
        prev = end
