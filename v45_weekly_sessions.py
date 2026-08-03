"""1) v4.5 weekly table + drawdown timeline on the REAL Fusion feed.
2) Real spread by UTC hour (when are spreads good?).
3) Session-window and spread-limit variants of v4.5 — find the best filter.
"""
from datetime import datetime, timedelta, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

V45 = dict(DEFAULT)
V45.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)
t = secs["t"]


def weekly(res, label):
    weeks = {}
    bal = 1000.0
    for c in res["cycles"]:
        bal += c["pnl"]
        d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
        monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
        weeks.setdefault(monday, []).append((bal, c["pnl"]))
    print(f"\n--- weekly: {label} (from $1,000) ---")
    print(f"{'week':<8}{'start':>9}{'end':>9}{'lowest':>9}{'net':>9}")
    prev = 1000.0
    for wk in sorted(weeks):
        rows = weeks[wk]
        end = rows[-1][0]
        lowest = min(prev, min(b for b, _ in rows))
        net = sum(p for _, p in rows)
        print(f"{wk:<8}{prev:>9.2f}{end:>9.2f}{lowest:>9.2f}{net:>+9.2f}")
        prev = end
    # drawdown timeline
    eq = peak = worst = 0.0
    peak_t = None
    win = (None, None)
    for c in res["cycles"]:
        eq += c["pnl"]
        if eq > peak:
            peak, peak_t = eq, c["t"]
        if eq - peak < worst:
            worst = eq - peak
            win = (peak_t, c["t"])
    f = lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%a %m-%d")
    if win[0]:
        print(f"maxDD {worst:+.2f}: peak {f(win[0])} -> trough {f(win[1])}")


print("=== 1) v4.5 baseline, real feed ===")
r_base = run(V45, secs, rng)
print(f"net {r_base['net']:+.2f} | maxDD {r_base['max_dd']:+.2f} | "
      f"{r_base['n']} cyc | {r_base['win_rate']*100:.0f}% wins")
weekly(r_base, "v4.5 all hours")

print("\n=== 2) real spread by UTC hour ===")
hours = (t // 3600) % 24
sp = secs["ask_c"] - secs["bid_c"]
for h in range(24):
    m = hours == h
    if m.sum():
        avg = sp[m].mean()
        print(f"  {h:02d} UTC: avg ${avg:.3f} {'#' * int(avg * 200)}")

print("\n=== 3) session windows & spread limits ===")
WINDOWS = [
    ("US 12-20", set(range(12, 20))),
    ("London 07-15", set(range(7, 15))),
    ("22-04 (Wajeh)", {22, 23, 0, 1, 2, 3}),
    ("00-04", {0, 1, 2, 3}),
    ("12-16 only", set(range(12, 16))),
    ("07-20 (Ldn+US)", set(range(7, 20))),
]
results = {}
for label, hrs in WINDOWS:
    r = run(dict(V45, hours=hrs), secs, rng)
    results[label] = r
    print(f"{label:<16}: net {r['net']:>+9.2f} | maxDD {r['max_dd']:>+9.2f} | "
          f"{r['n']:>4} cyc | {r['win_rate']*100:.0f}%")
for lim in (0.10, 0.08):
    r = run(dict(V45, max_spread=lim), secs, rng)
    results[f"spread<={lim}"] = r
    print(f"{f'spread<={lim}':<16}: net {r['net']:>+9.2f} | maxDD {r['max_dd']:>+9.2f} | "
          f"{r['n']:>4} cyc | {r['win_rate']*100:.0f}%")

best = max(results, key=lambda k: results[k]["net"])
if results[best]["net"] > r_base["net"]:
    weekly(results[best], f"BEST filter: {best}")
else:
    print(f"\n(no filter beats the all-hours baseline {r_base['net']:+.2f})")
