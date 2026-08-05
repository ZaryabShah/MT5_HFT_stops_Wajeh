"""Find tonight's first valid anchor (staged v4.8 conditions) and simulate
the OPEN cycle from there to the freshest tick: fills, floating P/L, and
distance to each exit — 'how the trade is running right now'."""
from datetime import datetime, timezone

import numpy as np

from backtest import adaptive_step, build_seconds, minute_ranges, raw_step

utc = timezone.utc
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
netm = np.abs(mcl[np.clip(pos, 0, None)] - mcl[np.clip(lo, 0, None)])
tot = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
er = np.where(tot > 1e-9, netm / np.maximum(tot, 1e-9), 0.0)
GATE = (lo >= 0) & (er >= 0.25) & (netm >= 3.0)

CFG = dict(step_mult=0.5, step_floor=0.30, step_cap=2.5)
t6 = int(datetime(2026, 8, 6, tzinfo=utc).timestamp())
i0 = np.searchsorted(t, t6)
hour = (t // 3600) % 24
spread = secs["ask_c"] - secs["bid_c"]

anchor_i = None
for i in range(i0, len(t)):
    if hour[i] not in {0, 1, 2, 3, 4, 5}:
        continue
    if not GATE[i] or spread[i] > 0.35:
        continue
    if raw_step(rng, t[i], CFG) < 6.0 * spread[i]:
        continue
    anchor_i = i
    break

if anchor_i is None:
    print("no valid anchor yet tonight — bot would still be waiting on gates")
else:
    i = anchor_i
    ts = datetime.fromtimestamp(int(t[i]), tz=utc)
    step = adaptive_step(rng, t[i], CFG)
    aa, ab = secs["ask_c"][i], secs["bid_c"][i]
    n_lv = 11
    basis = 0.01 * 100 * step * n_lv * (n_lv - 1) / 2 / 0.12
    target, maxloss = basis * 0.12, basis * 0.08
    buys = [round(aa + k * step, 3) for k in range(1, n_lv + 1)]
    sells = [round(ab - k * step, 3) for k in range(1, n_lv + 1)]
    longs, shorts = [], []
    realized, peak, purged = 0.0, 0.0, False
    COMM = 0.0225
    for j in range(i + 1, len(t)):
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        while buys and ah >= buys[0]:
            longs.append(max(buys.pop(0), ao))
            realized -= COMM
        while sells and bl <= sells[0]:
            shorts.append(min(sells.pop(0), bo))
            realized -= COMM
        if not purged:
            if len(longs) >= 5 and len(shorts) <= 2:
                realized += sum((e - ac) for e in shorts) * 1.0 - COMM * len(shorts)
                shorts, sells, purged = [], [], True
            elif len(shorts) >= 5 and len(longs) <= 2:
                realized += sum((bc - e) for e in longs) * 1.0 - COMM * len(longs)
                longs, buys, purged = [], [], True
        profit = realized + sum((bc - e) for e in longs) * 1.0 \
            + sum((e - ac) for e in shorts) * 1.0
        peak = max(peak, profit)
    now = datetime.fromtimestamp(int(t[-1]), tz=utc)
    print(f"ANCHOR fired {ts.strftime('%H:%M:%S')} server @ ask {aa:.2f} | "
          f"step {step:.2f} | target +{target:.2f} | SL -{maxloss:.2f}")
    print(f"as of {now.strftime('%H:%M:%S')}: {len(longs)} longs, "
          f"{len(shorts)} shorts open, purged={purged}")
    print(f"floating P/L {profit:+.2f} (peak was {peak:+.2f}) | "
          f"trail {'ARMED' if peak >= target * 0.5 else 'not armed'}")
    print(f"pendings left: {len(buys)} buys, {len(sells)} sells")
print("\nDONE open_cycle_now")
