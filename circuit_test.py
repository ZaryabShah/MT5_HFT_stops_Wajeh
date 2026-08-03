"""1) Daily-loss circuit breaker sweep over the 4 months (Fusion costs).
2) Autopsy of the catastrophic April 6-17 fortnight: what the market did and
   how the cycles died."""
from datetime import datetime, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

V42 = dict(DEFAULT)
V42.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=None, regime_mult=4.0,
                commission_per_lot_side=2.25))

secs = respread(build_seconds(), 0.031)
rng = minute_ranges(secs)
t = secs["t"]

APR6 = int(datetime(2026, 4, 6, tzinfo=timezone.utc).timestamp())
APR18 = int(datetime(2026, 4, 18, tzinfo=timezone.utc).timestamp())
JUN15 = int(datetime(2026, 6, 15, tzinfo=timezone.utc).timestamp())

print("=== circuit breaker sweep (4 months, Fusion costs) ===")
print(f"{'daily stop':>11} {'total net':>10} {'maxDD':>10} {'Apr6-17':>9} "
      f"{'Jun15-Jul31':>12} {'cycles':>7}")
results = {}
for L in (None, 50, 75, 100, 150):
    cfg = dict(V42, daily_stop=L)
    r = run(cfg, secs, rng)
    apr = sum(c["pnl"] for c in r["cycles"] if APR6 <= c["t"] < APR18)
    jun = sum(c["pnl"] for c in r["cycles"] if c["t"] >= JUN15)
    results[L] = r
    print(f"{str(L):>11} {r['net']:>+10.2f} {r['max_dd']:>+10.2f} {apr:>+9.2f} "
          f"{jun:>+12.2f} {r['n']:>7}")

# ---- autopsy of Apr 6-17 (no breaker) ----
print("\n=== APRIL 6-17 AUTOPSY ===")
mid = (secs["bid_c"] + secs["ask_c"]) / 2
print("daily price action:")
for d0 in range(APR6, APR18, 86400):
    lo_i, hi_i = np.searchsorted(t, d0), np.searchsorted(t, d0 + 86400)
    if hi_i - lo_i < 1000:
        continue
    m = mid[lo_i:hi_i]
    day = datetime.fromtimestamp(d0, tz=timezone.utc).strftime("%a %m-%d")
    print(f"  {day}: open {m[0]:8.1f} high {m.max():8.1f} low {m.min():8.1f} "
          f"close {m[-1]:8.1f} | range ${m.max() - m.min():6.1f} | "
          f"net move ${m[-1] - m[0]:+7.1f}")

r0 = results[None]
def stats(cycles, label):
    if not cycles:
        return
    outs = {}
    for c in cycles:
        outs.setdefault(c["outcome"], []).append(c["pnl"])
    wins = sum(1 for c in cycles if c["pnl"] > 0)
    step = np.mean([c["step"] for c in cycles])
    print(f"\n{label}: {len(cycles)} cycles, {100*wins/len(cycles):.0f}% wins, "
          f"avg step ${step:.2f}, net {sum(c['pnl'] for c in cycles):+.2f}")
    for o, pnls in sorted(outs.items()):
        print(f"    {o:<11} x{len(pnls):>4}  avg {np.mean(pnls):+7.2f}  "
              f"total {sum(pnls):+9.2f}")

stats([c for c in r0["cycles"] if APR6 <= c["t"] < APR18], "Apr 6-17 (disaster)")
stats([c for c in r0["cycles"] if c["t"] >= JUN15], "Jun 15-Jul 31 (good regime)")
