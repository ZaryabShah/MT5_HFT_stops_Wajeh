"""Full-detail weekly report for v4.6 (real Fusion feed, from $1,000):
start / end / lowest / highest balance, net, within-week max drawdown,
cycles, win rate."""
from datetime import datetime, timedelta, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run

V46 = dict(DEFAULT)
V46.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50,
                hours={22, 23, 0, 1, 2, 3, 4, 5}))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)
r = run(V46, secs, rng)

weeks = {}
bal = 1000.0
for c in r["cycles"]:
    bal += c["pnl"]
    d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
    monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
    weeks.setdefault(monday, []).append((bal, c["pnl"]))

print("v4.6 · real Fusion feed · 0.01 lots · from $1,000 · weekly detail\n")
print(f"{'week':<7}{'cyc':>4}{'W-L':>7}{'start':>9}{'end':>9}{'lowest':>9}"
      f"{'highest':>9}{'net':>9}{'wk maxDD':>10}")
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
          f"{end:>9.2f}{lowest:>9.2f}{highest:>9.2f}{net:>+9.2f}{dd:>+10.2f}")
    prev = end

print(f"\nTOTAL: {r['n']} cycles | {r['win_rate']*100:.0f}% wins | "
      f"net {r['net']:+.2f} | final {1000 + r['net']:.2f} | "
      f"overall maxDD {r['max_dd']:+.2f}")
