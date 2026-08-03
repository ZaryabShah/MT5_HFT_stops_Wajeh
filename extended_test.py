"""v4.2 over the full extended tick history: weekly breakdown, drawdown
windows, both cost models."""
from datetime import datetime, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from strategies import respread

V42 = dict(DEFAULT)
V42.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=None, regime_mult=4.0))


def fmt(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%a %m-%d %H:%M")


base = build_seconds()
t0, t1 = base["t"][0], base["t"][-1]
print(f"data: {fmt(t0)} -> {fmt(t1)} UTC "
      f"({(t1 - t0) / 86400:.0f} calendar days, {len(base['t']):,} seconds)")

for name, secs, comm in [("Exness Standard", base, 0.0),
                         ("Fusion ECN", respread(base, 0.031), 2.25)]:
    cfg = dict(V42, commission_per_lot_side=comm)
    rng = minute_ranges(secs)
    r = run(cfg, secs, rng)
    print(f"\n===== {name} =====")
    print(f"total: net {r['net']:+.2f} | {r['n']} cycles | "
          f"{r['win_rate'] * 100:.0f}% wins | maxDD {r['max_dd']:+.2f}")

    # weekly breakdown
    weeks = {}
    for c in r["cycles"]:
        wk = datetime.fromtimestamp(c["t"], tz=timezone.utc).strftime("%V")
        weeks.setdefault(wk, []).append(c["pnl"])
    print(f"{'week':>6} {'cycles':>7} {'net':>10}")
    for wk, pnls in weeks.items():
        print(f"{wk:>6} {len(pnls):>7} {sum(pnls):>+10.2f}")

    # worst drawdown window
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
    if win[0]:
        print(f"worst DD {worst:+.2f}: {fmt(win[0])} -> {fmt(win[1])}")
