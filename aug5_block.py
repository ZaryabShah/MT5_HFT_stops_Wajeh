"""Replay the 20-22 server block (17-19 UTC) of Aug 5 in isolation
(block-only hours, own daily breaker), on the freshest ticks available."""
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

utc = timezone.utc
assert mt5.initialize(login=426190, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
ticks = mt5.copy_ticks_range("XAUUSD", datetime(2026, 8, 4, tzinfo=utc),
                             datetime(2026, 8, 6, tzinfo=utc), mt5.COPY_TICKS_ALL)
mt5.shutdown()
last = datetime.fromtimestamp(int(ticks[-1]["time"]), tz=utc)
print(f"ticks: {len(ticks):,} | data through {last} server")
np.savez_compressed("data/ticks_aug5c.npz", ticks=np.array(ticks))
import os
for f in ("data/secs_aug5c.npz",):
    if os.path.exists(f):
        os.remove(f)
secs = build_seconds("data/ticks_aug5c.npz", "data/secs_aug5c.npz")
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
                daily_stop=50, hours={20, 21}, gate_series=GATE))
t5 = int(datetime(2026, 8, 5, tzinfo=utc).timestamp())
r = run(CFG, secs, rng, t_from=t5)
print(f"\nblock 20-22 server (17-19 UTC), Aug 5, block-only: "
      f"net {r['net']:+.2f} | {r['n']} cycles")
for c in r["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=utc)
    print(f"   end {d.strftime('%H:%M:%S')}  {c['outcome']:<11} "
          f"step {c['step']:.2f}  {c['pnl']:>+7.2f}")

# block tape anatomy
for h in (20, 21):
    lo_ = int(datetime(2026, 8, 5, h, tzinfo=utc).timestamp())
    i0, i1 = np.searchsorted(t, lo_), np.searchsorted(t, lo_ + 3600)
    if i1 - i0 < 60:
        print(f"   hour {h}: (no/partial data)")
        continue
    seg = mid[i0:i1]
    m2 = t[i0:i1] // 60
    u2, ix2 = np.unique(m2, return_index=True)
    mc2 = seg[np.append(ix2[1:], len(seg)) - 1]
    path = float(np.abs(np.diff(mc2)).sum())
    nt = float(mc2[-1] - mc2[0])
    print(f"   hour {h} tape: net {nt:+.2f} | path {path:.2f} | "
          f"ER {abs(nt) / path if path else 0:.2f}")
print("\nDONE aug5_block")
