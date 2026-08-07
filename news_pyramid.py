"""News-pyramid search (user spec): heavy first entry via stop at +/-D, then
0.01-lot layer stops every S$ beyond it (max 20/side), each position SL'd at
entry -/+ SLd. $200 account, 1:500, REAL margin + 20% stop-out modeled,
commission $2.25/lot/side. Close all at T+20min. 81 configs x 5 events."""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
z = np.load("data/secs_fusion.npz")
t = z["t"].astype(np.int64)
bid_c, ask_c = z["bid_c"], z["ask_c"]
bid_h, bid_l = z["bid_h"], z["bid_l"]
ask_h, ask_l = z["ask_h"], z["ask_l"]
bid_o, ask_o = z["bid_o"], z["ask_o"]

EVENTS = [
    ("May01 US-data", datetime(2026, 5, 1, 15, 26, tzinfo=utc)),
    ("Jun05 NFP", datetime(2026, 6, 5, 15, 30, tzinfo=utc)),
    ("Jun10 CPI", datetime(2026, 6, 10, 15, 30, tzinfo=utc)),
    ("Jun17 FOMC", datetime(2026, 6, 17, 21, 0, tzinfo=utc)),
    ("Jul14 CPI", datetime(2026, 7, 14, 15, 30, tzinfo=utc)),
]
STAKE, LEV, NL, LAYER = 200.0, 500.0, 20, 0.01


def sim(ev_epoch, D, L0, S, SLd, hold=1200):
    i0 = np.searchsorted(t, ev_epoch - 60)
    iend = np.searchsorted(t, ev_epoch + hold)
    if i0 >= len(t) or iend <= i0:
        return None
    mid0 = (bid_c[i0] + ask_c[i0]) / 2
    pend = []
    for k in range(NL + 1):
        lot = L0 if k == 0 else LAYER
        pend.append(["B", round(mid0 + D + k * S, 2), lot])
        pend.append(["S", round(mid0 - D - k * S, 2), lot])
    pos = []                    # [side, entry, lot, sl]
    realized = 0.0
    used = 0.0
    stopped = False
    fills = 0
    for j in range(i0, min(iend, len(t))):
        floating = sum((bid_c[j] - e) * 100 * lt if sd == "B"
                       else (e - ask_c[j]) * 100 * lt
                       for sd, e, lt, _ in pos)
        equity = STAKE + realized + floating
        # fills (margin-gated)
        still = []
        for p in pend:
            sd, lvl, lt = p
            hit = (sd == "B" and ask_h[j] >= lvl) or \
                  (sd == "S" and bid_l[j] <= lvl)
            if hit:
                px = max(lvl, ask_o[j]) if sd == "B" else min(lvl, bid_o[j])
                need = lt * 100 * px / LEV
                if equity - used >= need:
                    pos.append([sd, px, lt, px - SLd if sd == "B" else px + SLd])
                    used += need
                    realized -= 2.25 * lt
                    fills += 1
            else:
                still.append(p)
        pend = still
        # SLs
        keep = []
        for sd, e, lt, sl in pos:
            if sd == "B" and bid_l[j] <= sl:
                fill = min(sl, bid_o[j])
                realized += (fill - e) * 100 * lt - 2.25 * lt
                used -= lt * 100 * e / LEV
            elif sd == "S" and ask_h[j] >= sl:
                fill = max(sl, ask_o[j])
                realized += (e - fill) * 100 * lt - 2.25 * lt
                used -= lt * 100 * e / LEV
            else:
                keep.append([sd, e, lt, sl])
        pos = keep
        # stop-out
        floating = sum((bid_c[j] - e) * 100 * lt if sd == "B"
                       else (e - ask_c[j]) * 100 * lt
                       for sd, e, lt, _ in pos)
        equity = STAKE + realized + floating
        if used > 0 and equity <= 0.2 * used:
            for sd, e, lt, _ in pos:
                px = bid_c[j] if sd == "B" else ask_c[j]
                realized += ((px - e) if sd == "B" else (e - px)) * 100 * lt \
                    - 2.25 * lt
            pos = []
            stopped = True
            break
    j = min(iend, len(t) - 1)
    for sd, e, lt, _ in pos:
        px = bid_c[j] if sd == "B" else ask_c[j]
        realized += ((px - e) if sd == "B" else (e - px)) * 100 * lt - 2.25 * lt
    return realized, stopped, fills


results = []
for D in (2.0, 3.5, 5.0):
    for L0 in (0.05, 0.10, 0.23):
        for S in (0.25, 0.5, 1.0):
            for SLd in (4.0, 5.5, 8.0):
                per = []
                blows = 0
                for name, dtv in EVENTS:
                    r = sim(int(dtv.timestamp()), D, L0, S, SLd)
                    if r is None:
                        continue
                    per.append((name, r[0], r[1]))
                    blows += r[1]
                tot = sum(p for _, p, _ in per)
                results.append((tot, D, L0, S, SLd, per, blows))

results.sort(key=lambda x: -x[0])
prof = sum(1 for r in results if r[0] > 0)
print(f"configs profitable across all 5 events: {prof}/81\n")
print("TOP 8:")
for tot, D, L0, S, SLd, per, blows in results[:8]:
    ev = " ".join(f"{n.split()[0]}:{p:+.0f}{'X' if s else ''}" for n, p, s in per)
    print(f"  D={D} L0={L0} S={S} SL={SLd}: TOTAL {tot:+.0f} "
          f"(stopouts {blows}/5) | {ev}", flush=True)
print("\nWORST 3:")
for tot, D, L0, S, SLd, per, blows in results[-3:]:
    print(f"  D={D} L0={L0} S={S} SL={SLd}: TOTAL {tot:+.0f} "
          f"(stopouts {blows}/5)")
med = results[len(results) // 2][0]
print(f"\nmedian config total: {med:+.0f}")
print("\nDONE news_pyramid")
