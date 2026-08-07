"""Peak-profit analysis for the news pyramid (champion config): per event,
final P/L (T+20min close) vs PEAK equity P/L and its timing. Plus trailing
exits (close all on giveback from peak) vs the fixed hold."""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
z = np.load("data/secs_fusion.npz")
t = z["t"].astype(np.int64)
bid_c, ask_c = z["bid_c"], z["ask_c"]
bid_l, ask_h = z["bid_l"], z["ask_h"]
bid_o, ask_o = z["bid_o"], z["ask_o"]
spread = ask_c - bid_c

IS_EVENTS = [datetime(2026, 5, 1, 15, 26), datetime(2026, 6, 5, 15, 30),
             datetime(2026, 6, 10, 15, 30), datetime(2026, 6, 17, 21, 0),
             datetime(2026, 7, 14, 15, 30)]
IS_SET = {int(d.replace(tzinfo=utc).timestamp()) for d in IS_EVENTS}
days = np.unique(t // 86400)
EVENTS = sorted(IS_SET)
for d in days:
    for hh, mm in ((15, 30), (21, 0)):
        ev = int(d) * 86400 + hh * 3600 + mm * 60
        i0, i1 = np.searchsorted(t, ev - 90), np.searchsorted(t, ev + 120)
        if i1 - i0 >= 60 and float(spread[i0:i1].max()) >= 0.80 \
                and ev not in IS_SET:
            EVENTS.append(ev)
EVENTS = sorted(EVENTS)

D, L0, S, SLd = 3.5, 0.05, 0.5, 8.0
STAKE, LEV, NL, LAYER = 200.0, 500.0, 20, 0.01


def sim(ev, trail_arm=None, trail_gb=None, hold=1200):
    i0 = np.searchsorted(t, ev - 60)
    iend = min(np.searchsorted(t, ev + hold), len(t) - 1)
    mid0 = (bid_c[i0] + ask_c[i0]) / 2
    pend = []
    for k in range(NL + 1):
        lot = L0 if k == 0 else LAYER
        pend.append(["B", round(mid0 + D + k * S, 2), lot])
        pend.append(["S", round(mid0 - D - k * S, 2), lot])
    pos, realized, used = [], 0.0, 0.0
    peak, peak_ts = -1e9, 0
    for j in range(i0, iend):
        floating = sum((bid_c[j] - e) * 100 * lt if sd == "B"
                       else (e - ask_c[j]) * 100 * lt
                       for sd, e, lt, _ in pos)
        equity_pnl = realized + floating
        if equity_pnl > peak:
            peak, peak_ts = equity_pnl, int(t[j]) - ev
        # trailing exit
        if trail_arm is not None and peak >= trail_arm and \
                equity_pnl <= peak * (1 - trail_gb) and pos:
            for sd, e, lt, _ in pos:
                px = bid_c[j] if sd == "B" else ask_c[j]
                realized += ((px - e) if sd == "B" else (e - px)) * 100 * lt \
                    - 2.25 * lt
            return realized, peak, peak_ts
        still = []
        for p in pend:
            sd, lvl, lt = p
            if (sd == "B" and ask_h[j] >= lvl) or \
                    (sd == "S" and bid_l[j] <= lvl):
                px = max(lvl, ask_o[j]) if sd == "B" else min(lvl, bid_o[j])
                need = lt * 100 * px / LEV
                if STAKE + equity_pnl - used >= need:
                    pos.append([sd, px, lt,
                                px - SLd if sd == "B" else px + SLd])
                    used += need
                    realized -= 2.25 * lt
            else:
                still.append(p)
        pend = still
        keep = []
        for sd, e, lt, sl in pos:
            if sd == "B" and bid_l[j] <= sl:
                realized += (min(sl, bid_o[j]) - e) * 100 * lt - 2.25 * lt
                used -= lt * 100 * e / LEV
            elif sd == "S" and ask_h[j] >= sl:
                realized += (e - max(sl, ask_o[j])) * 100 * lt - 2.25 * lt
                used -= lt * 100 * e / LEV
            else:
                keep.append([sd, e, lt, sl])
        pos = keep
        floating = sum((bid_c[j] - e) * 100 * lt if sd == "B"
                       else (e - ask_c[j]) * 100 * lt
                       for sd, e, lt, _ in pos)
        if used > 0 and STAKE + realized + floating <= 0.2 * used:
            for sd, e, lt, _ in pos:
                px = bid_c[j] if sd == "B" else ask_c[j]
                realized += ((px - e) if sd == "B" else (e - px)) * 100 * lt \
                    - 2.25 * lt
            return realized, peak, peak_ts
        j += 1
    for sd, e, lt, _ in pos:
        px = bid_c[iend] if sd == "B" else ask_c[iend]
        realized += ((px - e) if sd == "B" else (e - px)) * 100 * lt - 2.25 * lt
    return realized, peak, peak_ts


print(f"{'event':<18}{'final':>9}{'PEAK':>9}{'peak at':>9}")
tot_f = tot_p = 0.0
for ev in EVENTS:
    f, p, pts = sim(ev)
    tot_f += f
    tot_p += max(p, 0)
    d0 = datetime.fromtimestamp(ev, tz=utc)
    print(f"{d0.strftime('%a %m-%d %H:%M'):<18}{f:>+9.0f}{p:>+9.0f}"
          f"{pts:>+8d}s", flush=True)
print(f"{'TOTAL':<18}{tot_f:>+9.0f}{tot_p:>+9.0f}  (peak col = unattainable ceiling)")

print("\n=== trailing exits vs fixed T+20min hold ===")
for arm, gb in ((50, 0.25), (50, 0.40), (100, 0.30)):
    tot = sum(sim(ev, trail_arm=arm, trail_gb=gb)[0] for ev in EVENTS)
    print(f"  arm ${arm}, giveback {int(gb * 100)}%: TOTAL {tot:+.0f}",
          flush=True)
print("\nDONE news_peak")
