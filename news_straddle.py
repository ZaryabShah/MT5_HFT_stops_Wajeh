"""User's news-straddle proposal, tested on real Jul 14 ticks:
$200 account, 1:500, 0.23 lots, buy+sell stops at +/-offset, SL 5.5.
Plus: second-by-second spread life around the release, and a 4-month scan
of every spread-blowout event (do releases always look like this?)."""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
z = np.load("data/secs_fusion.npz")
t = z["t"].astype(np.int64)
bid_c, ask_c = z["bid_c"], z["ask_c"]
bid_h, bid_l = z["bid_h"], z["bid_l"]
ask_h, ask_l = z["ask_h"], z["ask_l"]
bid_o, ask_o = z["bid_o"], z["ask_o"]
spread = ask_c - bid_c

REL = int(datetime(2026, 7, 14, 15, 30, tzinfo=utc).timestamp())

# ---- 1) spread life, second by second ----
print("=== spread timeline around the release (seconds where max spread) ===")
i0 = np.searchsorted(t, REL - 120)
i1 = np.searchsorted(t, REL + 420)
sp = ask_h[i0:i1] - bid_l[i0:i1]          # worst intra-second spread
tt = t[i0:i1] - REL
for thr in (0.5, 1.0, 2.0, 4.0):
    above = tt[sp >= thr]
    if len(above):
        print(f"  spread >= {thr:>4.1f}$: first {above[0]:+d}s, last "
              f"{above[-1]:+d}s, total {len(above)}s")
print(f"  peak spread: {sp.max():.2f}$ at {tt[np.argmax(sp)]:+d}s")

# ---- 2) the straddle, mechanically ----
print("\n=== straddle sim: $200, 0.23 lots, SL $5.5, placed 60s before ===")
LOT, STAKE, LEV = 0.23, 200.0, 500

for off in (2.0, 3.5, 5.0):
    place = np.searchsorted(t, REL - 60)
    mid0 = (bid_c[place] + ask_c[place]) / 2
    b_lvl, s_lvl = mid0 + off, mid0 - off
    legs = {}
    for j in range(place, np.searchsorted(t, REL + 600)):
        if "B" not in legs and ask_h[j] >= b_lvl:
            legs["B"] = (j, max(b_lvl, ask_o[j]))
        if "S" not in legs and bid_l[j] <= s_lvl:
            legs["S"] = (j, min(s_lvl, bid_o[j]))
        if len(legs) == 2:
            break
    out = []
    pnl_tot = 0.0
    for side, (j0, entry) in legs.items():
        sl = entry - 5.5 if side == "B" else entry + 5.5
        pnl = None
        for j in range(j0, np.searchsorted(t, REL + 1800)):
            if side == "B" and bid_l[j] <= sl:
                fill = min(sl, bid_o[j])
                pnl = (fill - entry) * 100 * LOT
                out.append((side, j0, entry, f"SL @{fill:.2f} t{t[j] - REL:+d}s",
                            pnl))
                break
            if side == "S" and ask_h[j] >= sl:
                fill = max(sl, ask_o[j])
                pnl = (entry - fill) * 100 * LOT
                out.append((side, j0, entry, f"SL @{fill:.2f} t{t[j] - REL:+d}s",
                            pnl))
                break
        if pnl is None:
            j = np.searchsorted(t, REL + 1800)
            px = bid_c[j] if side == "B" else ask_c[j]
            pnl = ((px - entry) if side == "B" else (entry - px)) * 100 * LOT
            out.append((side, j0, entry, f"open@+30min {px:.2f}", pnl))
        pnl_tot += pnl
    print(f"\n offset +/-{off}$ (levels {b_lvl:.2f}/{s_lvl:.2f}):")
    for side, j0, entry, exit_s, pnl in out:
        slip = entry - b_lvl if side == "B" else s_lvl - entry
        print(f"   {side}: filled t{t[j0] - REL:+d}s @ {entry:.2f} "
              f"(slippage {abs(slip):.2f}$) -> {exit_s} -> {pnl:+.2f}$")
    print(f"   TOTAL: {pnl_tot:+.2f}$ on ${STAKE} account"
          + ("  ** ACCOUNT BLOWN **" if pnl_tot <= -STAKE else ""))

# ---- 3) do all releases look like this? 4-month blowout scan ----
print("\n=== all spread-blowout events, Apr-Jul (spread >= $1.00) ===")
mask = (ask_c - bid_c) >= 1.0
idxs = np.where(mask)[0]
events = []
if len(idxs):
    start = idxs[0]
    prev = idxs[0]
    for k in idxs[1:]:
        if t[k] - t[prev] > 120:
            events.append((start, prev))
            start = k
        prev = k
    events.append((start, prev))
print(f"{'date/time (server)':<22}{'dur(s)':>7}{'peak spr':>9}{'1m move':>9}")
best = sorted(events, key=lambda e: -(ask_c[e[0]:e[1] + 1]
                                      - bid_c[e[0]:e[1] + 1]).max())[:12]
mid = (bid_c + ask_c) / 2
for a, bnd in sorted(best, key=lambda e: t[e[0]]):
    d0 = datetime.fromtimestamp(int(t[a]), tz=utc)
    dur = int(t[bnd] - t[a]) + 1
    pk = float((ask_c[a:bnd + 1] - bid_c[a:bnd + 1]).max())
    j2 = min(len(mid) - 1, np.searchsorted(t, t[a] + 60))
    mv = float(mid[j2] - mid[max(0, a - 5)])
    print(f"{d0.strftime('%a %m-%d %H:%M:%S'):<22}{dur:>7}{pk:>9.2f}{mv:>+9.2f}",
          flush=True)
print("\nDONE news_straddle")
