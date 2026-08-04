"""The 20-22 server (17-19 real UTC) block alone, full v4.8 stack: per-day
ledger for the final trading days + cycle-by-cycle detail. Cycles START in
the block; open cycles finish naturally (engine default)."""
from datetime import datetime, timezone

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
CFG = dict(DEFAULT)
CFG.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21}, gate_series=GATE))
r = run(CFG, secs, rng)
print(f"20-22 server block alone (= 17-19 real UTC), 4 months: "
      f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cyc | "
      f"{r['win_rate'] * 100:.0f}% wins\n")

days = {}
order = []
for c in r["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=timezone.utc).strftime("%a %m-%d")
    if d not in days:
        days[d] = []
        order.append(d)
    days[d].append(c)

print("--- last 10 trading days with block cycles (server dates) ---")
print(f"{'day':<11}{'cyc':>4}{'W-L':>6}{'net':>9}")
for d in order[-10:]:
    cs = days[d]
    w = sum(1 for c in cs if c["pnl"] > 0)
    print(f"{d:<11}{len(cs):>4}{str(w) + '-' + str(len(cs) - w):>6}"
          f"{sum(c['pnl'] for c in cs):>+9.2f}")

print("\n--- cycle-by-cycle, last 5 of those days (times = server) ---")
for d in order[-5:]:
    print(f"{d}:")
    for c in days[d]:
        end = datetime.fromtimestamp(int(c["t"]), tz=timezone.utc).strftime("%H:%M")
        print(f"   end {end}  {c['outcome']:<11} step {c['step']:.2f}  "
              f"{c['pnl']:>+7.2f}")
