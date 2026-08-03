"""Exclude the Apr 6-17 disaster fortnight, then run: no breaker / $50 / $250
(all cap 2.50, Fusion costs). Weekly tables + blow-up detection from $1,000.
Blow-up rule: a real account is dead when balance hits ~$30 (stop-out zone)."""
from datetime import datetime, timedelta, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                 purge_at=5, step_cap=2.5, regime_mult=4.0,
                 commission_per_lot_side=2.25))

APR6 = int(datetime(2026, 4, 6, tzinfo=timezone.utc).timestamp())
APR18 = int(datetime(2026, 4, 18, tzinfo=timezone.utc).timestamp())

secs = respread(build_seconds(), 0.031)
keep = (secs["t"] < APR6) | (secs["t"] >= APR18)
secs = {k: v[keep] for k, v in secs.items()}
rng = minute_ranges(secs)
print(f"data with Apr 6-17 removed: {len(secs['t']):,} seconds")

for label, L in [("NO breaker", None), ("$50 breaker", 50), ("$250 breaker", 250)]:
    r = run(dict(BASE, daily_stop=L), secs, rng)
    print(f"\n===== {label} (cap 2.50) =====")
    print(f"total: net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | "
          f"{r['n']} cycles | {r['win_rate']*100:.0f}% wins")
    weeks = {}
    bal = 1000.0
    blown = None
    for c in r["cycles"]:
        bal += c["pnl"]
        if blown is None and bal <= 30.0:
            blown = c["t"]
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
    if blown:
        print(f">>> BLEW UP (balance <= $30) at "
          f"{datetime.fromtimestamp(blown, tz=timezone.utc):%a %m-%d %H:%M} UTC — "
          f"rows after that are hypothetical")
    else:
        print(">>> survived the whole period from $1,000")
