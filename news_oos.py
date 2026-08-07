"""OOS test of the news pyramid: auto-detect ALL release-slot events in the
4 months (15:30 and 21:00 server slots where spread blew out >= $0.80),
exclude the 5 in-sample events, run the frozen top-3 configs on the rest."""
from datetime import datetime, timezone

import numpy as np

from news_pyramid import EVENTS, sim, t, ask_c, bid_c

utc = timezone.utc
spread = ask_c - bid_c
used = {int(dtv.timestamp()) for _, dtv in EVENTS}

days = np.unique(t // 86400)
found = []
for d in days:
    for hh, mm in ((15, 30), (21, 0)):
        ev = int(d) * 86400 + hh * 3600 + mm * 60
        i0 = np.searchsorted(t, ev - 90)
        i1 = np.searchsorted(t, ev + 120)
        if i1 - i0 < 60:
            continue
        pk = float(spread[i0:i1].max())
        if pk >= 0.80 and ev not in used:
            dt_ = datetime.fromtimestamp(ev, tz=utc)
            found.append((ev, dt_, pk))

print(f"new (out-of-sample) events found: {len(found)}")
CONFIGS = [
    ("D=5.0 L0=0.1 S=1.0 SL=8", 5.0, 0.10, 1.0, 8.0),
    ("D=3.5 L0=0.05 S=0.5 SL=8", 3.5, 0.05, 0.5, 8.0),
    ("D=2.0 L0=0.05 S=1.0 SL=8", 2.0, 0.05, 1.0, 8.0),
]
for label, D, L0, S, SLd in CONFIGS:
    tot = 0.0
    wins = 0
    rows = []
    for ev, dt_, pk in found:
        r = sim(ev, D, L0, S, SLd)
        if r is None:
            continue
        pnl, stopped, fills = r
        tot += pnl
        wins += pnl > 0
        rows.append((dt_, pk, pnl, stopped))
    print(f"\n{label}: OOS TOTAL {tot:+.0f} over {len(rows)} events "
          f"({wins} positive)")
    for dt_, pk, pnl, stopped in rows:
        print(f"   {dt_.strftime('%a %m-%d %H:%M')} (spr {pk:.2f}): "
              f"{pnl:+8.2f}{'  STOPOUT' if stopped else ''}", flush=True)
print("\nDONE news_oos")
