"""Real Fusion feed: quantify the spread-spike damage and test mid-triggered
virtual stops. Four runs: quote-trigger vs mid-trigger, x no breaker / $50."""
from datetime import datetime, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                 purge_at=5, step_cap=2.5, regime_mult=4.0,
                 commission_per_lot_side=2.25))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)

for trig_mid in (False, True):
    for L in (None, 50):
        r = run(dict(BASE, daily_stop=L, trigger_on_mid=trig_mid), secs, rng)
        bal = 1000.0
        low = 1000.0
        blown = None
        for c in r["cycles"]:
            bal += c["pnl"]
            low = min(low, bal)
            if blown is None and bal <= 30:
                blown = c["t"]
        tag = "MID-trigger " if trig_mid else "quote-trig  "
        brk = f"stop {L}" if L else "no stop"
        status = (f"BLEW UP {datetime.fromtimestamp(blown, tz=timezone.utc):%m-%d}"
                  if blown else "survived")
        print(f"{tag} {brk:>8}: net {r['net']:>+9.2f} | maxDD {r['max_dd']:>+9.2f} | "
              f"{r['n']:>4} cyc | {r['win_rate']*100:.0f}% | low {low:>8.2f} | {status}")
