"""RIDER v2: one-sided trend grid + no-fill timeout (re-anchor with a fresh
direction call when the guess was wrong). Timeout sweep + outcome stats."""
import numpy as np

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
b = np.append(idx, len(t))
mcl = mid[b[1:] - 1]
pos = np.searchsorted(uniq, mins) - 1
lo = pos - 30
signed = mcl[np.clip(pos, 0, None)] - mcl[np.clip(lo, 0, None)]
DIR = np.where(signed >= 0, 1, -1).astype(np.int8)

V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE, dir_series=DIR, counter_levels=0))

print(f"{'variant':<30}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}"
      f"{'stale':>7}{'$/live-cyc':>11}")
print(f"{'v4.8 baseline (ref)':<30}{'+4374.06':>10}{'-340.92':>10}{641:>6}"
      f"{'54%':>6}{'-':>7}{'+6.82':>11}")
for to in (300, 600, 900, 1800):
    r = run(dict(V48, nofill_timeout=to), secs, rng)
    stale = sum(1 for c in r["cycles"] if c["outcome"] == "stale")
    live = [c for c in r["cycles"] if c["outcome"] != "stale"]
    per = (sum(c["pnl"] for c in live) / len(live)) if live else 0
    print(f"RIDER timeout {to:>4}s{'':<12}{r['net']:>+10.2f}"
          f"{r['max_dd']:>+10.2f}{len(live):>6}"
          f"{100 * sum(1 for c in live if c['pnl'] > 0) / max(len(live), 1):>5.0f}%"
          f"{stale:>7}{per:>+11.2f}", flush=True)
print("\nDONE rider_test")
