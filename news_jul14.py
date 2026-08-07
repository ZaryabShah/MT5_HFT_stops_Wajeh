"""News forensics: Jul 14, 5:30 PKT (AM = 03:30 server / PM = 15:30 server).
Minute-by-minute tick anatomy around both candidates: price, range, spread,
biggest 1-second jump, tick rate."""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
z = np.load("data/secs_fusion.npz")
t = z["t"].astype(np.int64)
bid_c, ask_c = z["bid_c"], z["ask_c"]
bid_h, bid_l = z["bid_h"], z["bid_l"]
ask_h = z["ask_h"]
mid = (bid_c + ask_c) / 2
spread = ask_c - bid_c


def window(label, y, m, d, hh, mm, before=10, after=25):
    t0 = int(datetime(y, m, d, hh, mm, tzinfo=utc).timestamp())
    print(f"\n=== {label} (server {hh:02d}:{mm:02d}) ===")
    print(f"{'min':>7}{'close':>9}{'1m range':>9}{'max spr':>8}{'1s jump':>8}"
          f"{'ticksec':>8}")
    for k in range(-before, after):
        a = t0 + k * 60
        i0, i1 = np.searchsorted(t, a), np.searchsorted(t, a + 60)
        if i1 <= i0:
            print(f"{k:>+7}  (no ticks)")
            continue
        seg = slice(i0, i1)
        rng_ = mid[seg].max() - mid[seg].min()
        msp = spread[seg].max()
        jumps = np.abs(np.diff(mid[seg])) if i1 - i0 > 1 else np.array([0.0])
        mark = " <== " if k == 0 else ""
        print(f"{k:>+7}{mid[i1 - 1]:>9.2f}{rng_:>9.2f}{msp:>8.3f}"
              f"{jumps.max():>8.2f}{i1 - i0:>8}{mark}", flush=True)


window("5:30 AM PKT = 00:30 UTC", 2026, 7, 14, 3, 30)
window("5:30 PM PKT = 12:30 UTC (8:30 NY)", 2026, 7, 14, 15, 30)
print("\nDONE news_jul14")
