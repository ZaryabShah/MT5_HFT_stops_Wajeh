"""User challenge: 'today the US session is one-sided — how is it poison?'
1) Fetch today's ticks, measure the US hours (server 15-20) hour by hour.
2) Replay v4.8-with-US-hours on TODAY: what would it have earned?
3) The 4-month distribution of US-hours trading: how many days pay, how many
   bleed, and what the average nets out to."""
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
print(f"ticks fetched: {len(ticks):,} | last: "
      f"{datetime.fromtimestamp(int(ticks[-1]['time']), tz=utc)} (server)")
np.savez_compressed("data/ticks_aug5b.npz", ticks=np.array(ticks))
import os
if os.path.exists("data/secs_aug5b.npz"):
    os.remove("data/secs_aug5b.npz")
secs = build_seconds("data/ticks_aug5b.npz", "data/secs_aug5b.npz")
rng = minute_ranges(secs)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2

# --- 1) today's US hours, hour by hour ---
print("\n=== TODAY (Aug 5 server), hour by hour ===")
print(f"{'srv hr':>7}{'net move':>10}{'path':>8}{'ER':>6}{'1m-rng avg':>11}")
for h in range(12, 21):
    lo = int(datetime(2026, 8, 5, h, tzinfo=utc).timestamp())
    hi = lo + 3600
    i0, i1 = np.searchsorted(t, lo), np.searchsorted(t, hi)
    if i1 - i0 < 100:
        continue
    seg = mid[i0:i1]
    mins = t[i0:i1] // 60
    u, ix = np.unique(mins, return_index=True)
    mcl = seg[np.append(ix[1:], len(seg)) - 1]
    path = float(np.abs(np.diff(mcl)).sum())
    net = float(mcl[-1] - mcl[0])
    rgs = [np.ptp(seg[ix[k]:(ix[k + 1] if k + 1 < len(ix) else len(seg))])
           for k in range(len(ix))]
    er = abs(net) / path if path > 0 else 0
    print(f"{h:>7}{net:>+10.2f}{path:>8.2f}{er:>6.2f}{np.mean(rgs):>11.2f}",
          flush=True)

# --- 2) replay v4.8 with US hours on today ---
from trend_gate import er_series, move_series  # noqa: E402  (gold 4mo gates)
mid_ = mid
mins_ = t // 60
u_, ix_ = np.unique(mins_, return_index=True)
b_ = np.append(ix_, len(t))
mcl_ = mid_[b_[1:] - 1]
pref = np.cumsum(np.abs(np.diff(mcl_, prepend=mcl_[0])))
pos = np.searchsorted(u_, mins_) - 1
lo_ = pos - 30
net_ = np.abs(mcl_[np.clip(pos, 0, None)] - mcl_[np.clip(lo_, 0, None)])
tot_ = pref[np.clip(pos, 0, None)] - pref[np.clip(lo_, 0, None)]
er_ = np.where(tot_ > 1e-9, net_ / np.maximum(tot_, 1e-9), 0.0)
GATE_TODAY = (lo_ >= 0) & (er_ >= 0.25) & (net_ >= 3.0)

US = {15, 16, 17, 18, 19}
CFG = dict(DEFAULT)
CFG.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours=US, gate_series=GATE_TODAY))
t5 = int(datetime(2026, 8, 5, tzinfo=utc).timestamp())
r = run(CFG, secs, rng, t_from=t5)
print(f"\n=== v4.8 stack, US hours 15-20, TODAY: net {r['net']:+.2f} | "
      f"{r['n']} cycles ===")
for c in r["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=utc)
    print(f"   end {d.strftime('%H:%M')}  {c['outcome']:<11} "
          f"step {c['step']:.2f}  {c['pnl']:>+7.2f}", flush=True)

# --- 3) the 4-month daily distribution of US-hours trading ---
from trend_gate import secs as gsecs  # noqa: E402
grng = minute_ranges(gsecs)
GGATE = er_series(30, 0.25) & move_series(30, 3.0)
rr = run(dict(CFG, gate_series=GGATE), gsecs, grng)
days = {}
for c in rr["cycles"]:
    days.setdefault(c["t"] // 86400, 0.0)
    days[c["t"] // 86400] += c["pnl"]
vals = np.array(sorted(days.values()))
pos_d = vals[vals > 0]
neg_d = vals[vals < 0]
print(f"\n=== 4 MONTHS of US-hours trading (same stack): net {rr['net']:+.2f} "
      f"| maxDD {rr['max_dd']:+.2f} ===")
print(f"trading days: {len(vals)} | winning days: {len(pos_d)} "
      f"(avg {pos_d.mean():+.2f}, best {pos_d.max():+.2f}) | losing days: "
      f"{len(neg_d)} (avg {neg_d.mean():+.2f}, worst {neg_d.min():+.2f})")
print(f"day P/L deciles: " + " ".join(
    f"{np.percentile(vals, p):+.0f}" for p in (10, 25, 50, 75, 90)))
print("\nDONE us_check")
