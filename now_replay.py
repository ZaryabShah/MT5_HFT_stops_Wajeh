"""What would the STAGED v4.8 bot be doing RIGHT NOW? Replay the new server
day (Aug 6, from the 01:00 reopen) on the freshest ticks."""
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

utc = timezone.utc
assert mt5.initialize(login=429466, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
ticks = mt5.copy_ticks_range("XAUUSD", datetime(2026, 8, 5, tzinfo=utc),
                             datetime(2026, 8, 7, tzinfo=utc), mt5.COPY_TICKS_ALL)
mt5.shutdown()
last = datetime.fromtimestamp(int(ticks[-1]["time"]), tz=utc)
print(f"data through {last} server")
np.savez_compressed("data/ticks_now.npz", ticks=np.array(ticks))
import os
if os.path.exists("data/secs_now.npz"):
    os.remove("data/secs_now.npz")
secs = build_seconds("data/ticks_now.npz", "data/secs_now.npz")
rng = minute_ranges(secs)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2

mins = t // 60
u, ix = np.unique(mins, return_index=True)
b = np.append(ix, len(t))
mcl = mid[b[1:] - 1]
pref = np.cumsum(np.abs(np.diff(mcl, prepend=mcl[0])))
pos = np.searchsorted(u, mins) - 1
lo = pos - 30
net = np.abs(mcl[np.clip(pos, 0, None)] - mcl[np.clip(lo, 0, None)])
tot = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
er = np.where(tot > 1e-9, net / np.maximum(tot, 1e-9), 0.0)
GATE = (lo >= 0) & (er >= 0.25) & (net >= 3.0)

CFG = dict(DEFAULT)
CFG.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))
t6 = int(datetime(2026, 8, 6, tzinfo=utc).timestamp())
r = run(CFG, secs, rng, t_from=t6)
print(f"\nSTAGED bot, server day Aug 6 so far: net {r['net']:+.2f} | "
      f"{r['n']} cycles")
for c in r["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=utc)
    print(f"   end {d.strftime('%H:%M:%S')}  {c['outcome']:<11} "
          f"step {c['step']:.2f}  {c['pnl']:>+7.2f}")

# state at the freshest second
j = len(t) - 1
print(f"\nstate at {last.strftime('%H:%M:%S')} server:")
print(f"   trend gate: {'PASS' if GATE[j] else 'fail'} "
      f"(ER {er[j]:.2f}, move30m {net[j]:.2f})")
last_end = r["cycles"][-1]["t"] if r["cycles"] else None
if last_end:
    print(f"   last cycle closed {int(t[j]) - int(last_end)}s ago")
day_pnl = r["net"]
print(f"   day P/L {day_pnl:+.2f} (breaker at -50): "
      f"{'TRIPPED - flat until next server day' if day_pnl <= -50 else 'armed'}")
print("\nDONE now_replay")
