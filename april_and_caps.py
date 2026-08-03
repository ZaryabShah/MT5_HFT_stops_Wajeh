"""A) April day-by-day P/L (v4.2, no breaker): which days did the damage?
B) Step-cap sweep over 4 months WITH the $50 daily breaker.
C) Weekly tables for the interesting caps."""
from datetime import datetime, timedelta, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                 purge_at=5, step_cap=None, regime_mult=4.0,
                 commission_per_lot_side=2.25))

secs = respread(build_seconds(), 0.031)
rng = minute_ranges(secs)


def daily_table(res, d_from, d_to):
    days = {}
    for c in res["cycles"]:
        if d_from <= c["t"] < d_to:
            d = datetime.fromtimestamp(c["t"], tz=timezone.utc).strftime("%a %m-%d")
            days.setdefault(d, []).append(c)
    print(f"{'day':<11}{'cycles':>7}{'net':>10}{'avg step':>9}{'max step':>9}")
    for d, cs in days.items():
        net = sum(c["pnl"] for c in cs)
        steps = [c["step"] for c in cs]
        mark = " <<<" if net < -100 else ""
        print(f"{d:<11}{len(cs):>7}{net:>+10.2f}{np.mean(steps):>9.2f}"
              f"{max(steps):>9.2f}{mark}")


def weekly_table(res, label):
    weeks = {}
    bal = 1000.0
    for c in res["cycles"]:
        bal += c["pnl"]
        d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
        monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
        weeks.setdefault(monday, []).append((bal, c["pnl"]))
    print(f"\n--- weekly: {label} ---")
    print(f"{'week':<8}{'start':>9}{'end':>9}{'lowest':>9}{'net':>9}")
    prev = 1000.0
    for wk in sorted(weeks):
        rows = weeks[wk]
        end = rows[-1][0]
        lowest = min(prev, min(b for b, _ in rows))
        net = sum(p for _, p in rows)
        print(f"{wk:<8}{prev:>9.2f}{end:>9.2f}{lowest:>9.2f}{net:>+9.2f}")
        prev = end


APR1 = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
MAY1 = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp())

print("=== A) APRIL, day by day (v4.2, no breaker) ===")
r_nobrk = run(BASE, secs, rng)
daily_table(r_nobrk, APR1, MAY1)
apr = [c for c in r_nobrk["cycles"] if APR1 <= c["t"] < MAY1]
neg_days = {}
for c in apr:
    d = datetime.fromtimestamp(c["t"], tz=timezone.utc).strftime("%m-%d")
    neg_days[d] = neg_days.get(d, 0) + c["pnl"]
worst = sorted(neg_days.items(), key=lambda x: x[1])[:5]
best = sorted(neg_days.items(), key=lambda x: -x[1])[:5]
print(f"\nApril total: {sum(neg_days.values()):+.2f} over {len(neg_days)} days")
print(f"5 worst days: {', '.join(f'{d} {p:+.0f}' for d, p in worst)} "
      f"= {sum(p for _, p in worst):+.2f}")
print(f"5 best days:  {', '.join(f'{d} {p:+.0f}' for d, p in best)} "
      f"= {sum(p for _, p in best):+.2f}")

print("\n=== B) step-cap sweep, 4 months, WITH $50 daily breaker ===")
print(f"{'cap':>6} {'total net':>10} {'maxDD':>10} {'April net':>10} {'cycles':>7}")
results = {}
for cap in (0.90, 1.20, 1.50, 2.00, 2.50, None):
    cfg = dict(BASE, step_cap=cap, daily_stop=50)
    r = run(cfg, secs, rng)
    apr_net = sum(c["pnl"] for c in r["cycles"] if APR1 <= c["t"] < MAY1)
    results[cap] = r
    print(f"{str(cap):>6} {r['net']:>+10.2f} {r['max_dd']:>+10.2f} "
          f"{apr_net:>+10.2f} {r['n']:>7}")

print("\n=== C) weekly detail ===")
weekly_table(results[None], "no cap + $50 breaker (current v4.3)")
best_cap = max((k for k in results if k), key=lambda k: results[k]["net"])
weekly_table(results[best_cap], f"cap {best_cap} + $50 breaker")
