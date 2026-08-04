"""Replay Aug 3-5 REAL Fusion ticks through the v4.8 engine.
Focus: the 20-22 server block (= 17-19 real UTC) on server day Aug 4.
Self-contained gate computation (trend_gate.py is bound to the 4-month file)."""
from datetime import datetime, timezone

import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

secs = build_seconds("data/ticks_aug.npz", "data/secs_aug.npz")
rng = minute_ranges(secs)

# v4.7 trend gate, inline (ER(30m)>=0.25 AND |move30m|>=$3, closed minutes)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
bounds = np.append(idx, len(t))
m_close = mid[bounds[1:] - 1]
pref = np.cumsum(np.abs(np.diff(m_close, prepend=m_close[0])))
pos = np.searchsorted(uniq, mins) - 1
lo = pos - 30
ok = lo >= 0
net = np.abs(m_close[np.clip(pos, 0, None)] - m_close[np.clip(lo, 0, None)])
tot = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
er = np.where(tot > 1e-9, net / np.maximum(tot, 1e-9), 0.0)
GATE = ok & (er >= 0.25) & (net >= 3.0)

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                 step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                 daily_stop=50, gate_series=GATE))
utc = timezone.utc


def daily(label, r):
    print(f"{label}: net {r['net']:+.2f} | {r['n']} cyc")
    for c in r["cycles"]:
        d = datetime.fromtimestamp(int(c["t"]), tz=utc)
        print(f"   {d.strftime('%a %m-%d %H:%M')}  {c['outcome']:<11} "
              f"step {c['step']:.2f}  {c['pnl']:>+7.2f}")


print("=== full v4.8 window {20,21,0-5}, Aug 3-5 ===")
daily("all cycles", run(dict(BASE, hours={20, 21, 0, 1, 2, 3, 4, 5}), secs, rng))

print("\n=== 20-22 server block ONLY (= 17-19 real UTC) ===")
daily("block cycles", run(dict(BASE, hours={20, 21}), secs, rng))

# tape context for Aug 4 block hours
i0 = np.searchsorted(t, int(datetime(2026, 8, 4, 19, 30, tzinfo=utc).timestamp()))
i1 = np.searchsorted(t, int(datetime(2026, 8, 4, 22, 0, tzinfo=utc).timestamp()))
seg = slice(i0, i1)
print(f"\n=== tape, Aug 4 server 19:30-22:00 (= 16:30-19:00 UTC) ===")
print(f"bid range {secs['bid_l'][seg].min():.2f} - {secs['bid_h'][seg].max():.2f} "
      f"| net move {mid[i1 - 1] - mid[i0]:+.2f} "
      f"| avg spread {np.mean(secs['ask_c'][seg] - secs['bid_c'][seg]):.3f}")
for hh, mm in ((20, 0), (20, 30), (21, 0), (21, 30)):
    k = np.searchsorted(t, int(datetime(2026, 8, 4, hh, mm, tzinfo=utc).timestamp()))
    if k < len(t):
        print(f"   {hh:02d}:{mm:02d} server: gate {'PASS' if GATE[k] else 'fail'} "
              f"(ER {er[k]:.2f}, move30m ${net[k]:.2f})")
