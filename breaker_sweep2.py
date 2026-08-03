"""Daily-breaker sweep $50-$300 (step $50), cap fixed at 2.50, 4 months,
Fusion costs. Weekly table + start-time robustness for the best value."""
from datetime import datetime, timedelta, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                 purge_at=5, step_cap=2.5, regime_mult=4.0,
                 commission_per_lot_side=2.25))

secs = respread(build_seconds(), 0.031)
rng = minute_ranges(secs)
APR1 = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
MAY1 = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp())

print("=== daily breaker sweep (cap 2.50, 4 months, Fusion costs) ===")
print(f"{'breaker':>8} {'total net':>10} {'maxDD':>10} {'April':>9} {'cycles':>7}")
results = {}
for L in (50, 100, 150, 200, 250, 300):
    r = run(dict(BASE, daily_stop=L), secs, rng)
    apr = sum(c["pnl"] for c in r["cycles"] if APR1 <= c["t"] < MAY1)
    results[L] = r
    print(f"{L:>8} {r['net']:>+10.2f} {r['max_dd']:>+10.2f} {apr:>+9.2f} {r['n']:>7}")

best = max(results, key=lambda k: results[k]["net"])
print(f"\nbest by net: ${best}")

print(f"\n=== weekly table: breaker ${best}, cap 2.50, from $1,000 ===")
weeks = {}
bal = 1000.0
for c in results[best]["cycles"]:
    bal += c["pnl"]
    d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
    monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
    weeks.setdefault(monday, []).append((bal, c["pnl"]))
print(f"{'week':<8}{'start':>9}{'end':>9}{'lowest':>9}{'net':>9}")
prev = 1000.0
for wk in sorted(weeks):
    rows = weeks[wk]
    end = rows[-1][0]
    lowest = min(prev, min(b for b, _ in rows))
    net = sum(p for _, p in rows)
    print(f"{wk:<8}{prev:>9.2f}{end:>9.2f}{lowest:>9.2f}{net:>+9.2f}")
    prev = end

print(f"\n=== robustness: breaker ${best} from 5 start times ===")
t0 = int(secs["t"][0])
for off in (0, 900, 3600, 14400, 86400):
    idx = int(np.searchsorted(secs["t"], t0 + off))
    sub = {k: v[idx:] for k, v in secs.items()}
    r = run(dict(BASE, daily_stop=best), sub, rng)
    print(f"start +{off:>6}s: net {r['net']:+9.2f} | maxDD {r['max_dd']:+9.2f}")
