"""1) The finalized live config (no breaker, cap 2.50) over the FULL 4 months
   including April — the risk number for what launches Monday.
2) v5 lottery tickets over 4 months: spacing sweep, Fusion costs, flat 0.01,
   unlimited budget -> worst-ever account level, would $1k / $5k have died?
"""
from datetime import datetime, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run
from backtest_v5 import run_v5
from strategies import respread

COMM_RT = 0.045          # Fusion commission per 0.01 lot round trip

secs = respread(build_seconds(), 0.031)
rng = minute_ranges(secs)

print("=== finalized live config (cap 2.50, NO breaker), full 4 months ===")
cfg = dict(DEFAULT)
cfg.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=2.5, regime_mult=4.0,
                commission_per_lot_side=2.25, daily_stop=None))
r = run(cfg, secs, rng)
bal = 1000.0
low = 1000.0
blown = None
for c in r["cycles"]:
    bal += c["pnl"]
    if bal < low:
        low = bal
    if blown is None and bal <= 30:
        blown = c["t"]
print(f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cycles | "
      f"final {1000 + r['net']:.2f} | lowest {low:.2f}"
      + (f" | BLEW UP {datetime.fromtimestamp(blown, tz=timezone.utc):%m-%d %H:%M}"
         if blown else " | survived from $1,000"))

print("\n=== v5 lottery tickets, 4 months, Fusion costs, 0.01 lots, "
      "target +$49.5, unlimited budget ===")
print(f"{'step':>6} {'wins':>5} {'net(comm)':>11} {'worstAcct':>10} "
      f"{'$1k?':>6} {'$5k?':>6} {'openEnd':>9}")
for step in (0.20, 0.30, 0.45, 0.60, 0.90, 1.50):
    eps = run_v5(secs, step=step, target_usd=49.5, abort_dd=1_000_000)
    fills = sum(e["fills"] for e in eps)
    net = sum(e["pnl"] for e in eps) - fills * COMM_RT
    wins = sum(1 for e in eps if e["outcome"] == "target")
    openend = [e for e in eps if e["outcome"] == "OPEN_AT_END"]
    # worst account level from $0 baseline: cumulative before episode + its min
    cum = 0.0
    worst_acct = 0.0
    for e in eps:
        worst_acct = min(worst_acct, cum + e["min_dd"])
        cum += e["pnl"]
    dead1k = "DEAD" if worst_acct <= -970 else "ok"
    dead5k = "DEAD" if worst_acct <= -4970 else "ok"
    oe = f"{openend[0]['pnl']:+.0f}" if openend else "-"
    print(f"{step:>6.2f} {wins:>5} {net:>+11.2f} {worst_acct:>+10.2f} "
          f"{dead1k:>6} {dead5k:>6} {oe:>9}")
