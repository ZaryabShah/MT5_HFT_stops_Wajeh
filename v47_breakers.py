"""v4.7 with daily breaker None / $50 / $250: full weekly detail tables
(start/end/lowest/highest/net/week-maxDD/cycles/W-L) on the real feed."""
from datetime import datetime, timedelta, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run
from trend_gate import er_series, move_series

V47 = dict(DEFAULT)
V47.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25,
                hours={22, 23, 0, 1, 2, 3, 4, 5}))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)
gate = er_series(30, 0.25) & move_series(30, 3.0)

for label, L in [("NO breaker", None), ("$50 breaker (staged)", 50),
                 ("$250 breaker", 250)]:
    r = run(dict(V47, daily_stop=L, gate_series=gate), secs, rng)
    weeks = {}
    bal = 1000.0
    low_ever = 1000.0
    for c in r["cycles"]:
        bal += c["pnl"]
        low_ever = min(low_ever, bal)
        d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
        monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
        weeks.setdefault(monday, []).append((bal, c["pnl"]))
    print(f"\n===== v4.7, {label} =====")
    print(f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cyc | "
          f"{r['win_rate']*100:.0f}% wins | final {1000 + r['net']:.2f} | "
          f"lowest ever {low_ever:.2f}")
    print(f"{'week':<7}{'cyc':>4}{'W-L':>7}{'start':>9}{'end':>9}{'lowest':>9}"
          f"{'highest':>9}{'net':>9}{'wk DD':>9}")
    prev = 1000.0
    for wk in sorted(weeks):
        rows = weeks[wk]
        bals = [b for b, _ in rows]
        end = bals[-1]
        lowest = min(prev, min(bals))
        highest = max(prev, max(bals))
        net = sum(p for _, p in rows)
        wins = sum(1 for _, p in rows if p > 0)
        peak = prev
        dd = 0.0
        for b in bals:
            peak = max(peak, b)
            dd = min(dd, b - peak)
        print(f"{wk:<7}{len(rows):>4}{f'{wins}-{len(rows)-wins}':>7}{prev:>9.2f}"
              f"{end:>9.2f}{lowest:>9.2f}{highest:>9.2f}{net:>+9.2f}{dd:>+9.2f}")
        prev = end
