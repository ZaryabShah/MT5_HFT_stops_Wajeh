"""v4.2 on Fusion's own tick history: per-week start/end/lowest balance,
weekly P/L, and overall max drawdown."""
from datetime import datetime, timedelta, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run

START_BALANCE = 1000.00        # ~ the Fusion demo balance

V42 = dict(DEFAULT)
V42.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=None, regime_mult=4.0,
                commission_per_lot_side=2.25))

import os

from strategies import respread

if os.path.exists("data/ticks_fusion.npz"):
    secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
    src = "genuine Fusion ticks"
else:
    secs = respread(build_seconds(), 0.031)   # Exness ticks, Fusion spread model
    src = "Exness ticks + Fusion cost model (spread 0.062, comm $2.25/side)"
rng = minute_ranges(secs)
t0, t1 = secs["t"][0], secs["t"][-1]
print(f"source: {src}")
print(f"data: "
      f"{datetime.fromtimestamp(int(t0), tz=timezone.utc):%a %Y-%m-%d} -> "
      f"{datetime.fromtimestamp(int(t1), tz=timezone.utc):%a %Y-%m-%d} UTC, "
      f"{len(secs['t']):,} seconds")

r = run(V42, secs, rng)

# weekly accounting on the running balance
weeks = {}          # monday-date -> list of (t, balance_after_cycle, pnl)
bal = START_BALANCE
for c in r["cycles"]:
    bal += c["pnl"]
    d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
    monday = (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")
    weeks.setdefault(monday, []).append((c["t"], bal, c["pnl"]))

print(f"\nstart balance {START_BALANCE:.2f}, fixed 0.01 lots\n")
print(f"{'week (Mon)':<12}{'cycles':>7}{'start':>10}{'end':>10}{'lowest':>10}"
      f"{'net':>10}")
prev_end = START_BALANCE
for monday in sorted(weeks):
    rows = weeks[monday]
    start = prev_end
    end = rows[-1][1]
    lowest = min(start, min(b for _, b, _ in rows))
    net = sum(p for _, _, p in rows)
    print(f"{monday:<12}{len(rows):>7}{start:>10.2f}{end:>10.2f}{lowest:>10.2f}"
          f"{net:>+10.2f}")
    prev_end = end

# overall max drawdown with dates
eq = peak = worst = 0.0
peak_t = None
win = (None, None)
for c in r["cycles"]:
    eq += c["pnl"]
    if eq > peak:
        peak, peak_t = eq, c["t"]
    if eq - peak < worst:
        worst = eq - peak
        win = (peak_t, c["t"])
f = lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%a %m-%d %H:%M")
print(f"\nTOTAL: net {r['net']:+.2f} | {r['n']} cycles | "
      f"{r['win_rate']*100:.0f}% wins | final balance {prev_end:.2f}")
print(f"MAX DRAWDOWN {worst:+.2f}: peak {f(win[0])} -> trough {f(win[1])} UTC")
