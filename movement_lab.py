"""MOVEMENT-STYLE STRATEGY LAB (user mandate 08-05): single-position
strategies built from gold's MEASURED behaviors, real Fusion feed.
Families:
  ORB      opening-range breakout at session opens (01:00 / 20:00 server)
  SQUEEZE  volatility-compression breakout (tight 30m box -> expansion)
  CONT15   15-min momentum continuation, PULLBACK entry (measured: $2.5-5.8
           15-min moves continue 57%)
  EXHAUST  exhaustion fade after >$9/15min bursts (measured: snap back)
Protocol: IS = Apr-May (tuning), OOS = Jun-Jul (untouched judge).
Costs: real bid/ask entries/exits + $0.045/0.01-lot RT commission."""
from datetime import datetime, timezone

import numpy as np

from trend_gate import secs

CONTRACT, LOT, COMM_RT = 100.0, 0.01, 0.045
t = secs["t"].astype(np.int64)
n = len(t)
mid = (secs["bid_c"] + secs["ask_c"]) / 2
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
bounds = np.append(idx, n)
mc = mid[bounds[1:] - 1]
mh = np.array([mid[bounds[i]:bounds[i + 1]].max() for i in range(len(uniq))])
ml = np.array([mid[bounds[i]:bounds[i + 1]].min() for i in range(len(uniq))])
m_hour = (uniq * 60 // 3600) % 24
m_sec0 = idx                     # first second-index of each minute
JUN1 = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())


def sim(i0, d, sl, tp=None, trail_arm=None, trail_gb=None, timeout=7200):
    """Walk seconds from i0. d=+1 long/-1 short. Returns (pnl$, exit_sec_idx)."""
    entry = secs["ask_c"][i0] if d > 0 else secs["bid_c"][i0]
    peak = -1e9
    j = i0 + 1
    while j < n and t[j] - t[i0] < timeout:
        if d > 0:
            if secs["bid_l"][j] <= entry - sl:
                return (-sl * CONTRACT * LOT - COMM_RT, j)
            if tp and secs["bid_h"][j] >= entry + tp:
                return (tp * CONTRACT * LOT - COMM_RT, j)
            pnl = secs["bid_c"][j] - entry
        else:
            if secs["ask_h"][j] >= entry + sl:
                return (-sl * CONTRACT * LOT - COMM_RT, j)
            if tp and secs["ask_l"][j] <= entry - tp:
                return (tp * CONTRACT * LOT - COMM_RT, j)
            pnl = entry - secs["ask_c"][j]
        peak = max(peak, pnl)
        if trail_arm and peak >= trail_arm and pnl <= peak - trail_gb:
            return (pnl * CONTRACT * LOT - COMM_RT, j)
        j += 1
    j = min(j, n - 1)
    pnl = (secs["bid_c"][j] - entry) if d > 0 else (entry - secs["ask_c"][j])
    return (pnl * CONTRACT * LOT - COMM_RT, j)


def report(name, trades):
    for half, lohi in (("IS ", lambda ts: ts < JUN1), ("OOS", lambda ts: ts >= JUN1)):
        sub = [p for ts, p in trades if lohi(ts)]
        if not sub:
            print(f"  {name} {half}: no trades", flush=True)
            continue
        net = sum(sub)
        w = sum(1 for p in sub if p > 0)
        eq = np.cumsum(sub)
        dd = float(np.min(eq - np.maximum.accumulate(eq)))
        print(f"  {name} {half}: net {net:>+8.2f} | {len(sub):>4} trades | "
              f"{100 * w / len(sub):>3.0f}% | maxDD {dd:>+8.2f}", flush=True)


def orb(open_hour, box_min=20, brk=0.3, sl_cap=4.0):
    trades = []
    i = 1
    while i < len(uniq):
        if m_hour[i] == open_hour and m_hour[i - 1] != open_hour:
            if i + box_min + 2 >= len(uniq):
                break
            hi = mh[i:i + box_min].max()
            lo = ml[i:i + box_min].min()
            for k in range(i + box_min, min(i + box_min + 240, len(uniq) - 1)):
                d = 1 if mh[k] >= hi + brk else (-1 if ml[k] <= lo - brk else 0)
                if d:
                    sl = min(sl_cap, (hi - lo) + brk)
                    pnl, jx = sim(m_sec0[k + 1], d, sl,
                                  trail_arm=2.0, trail_gb=1.2, timeout=4 * 3600)
                    trades.append((int(t[m_sec0[k]]), pnl))
                    i = np.searchsorted(m_sec0, jx)
                    break
        i += 1
    return trades


def squeeze(width_mult=0.45, brk=0.3, hours=None):
    r30 = np.array([mh[max(0, i - 30):i].max() - ml[max(0, i - 30):i].min()
                    if i >= 30 else 9e9 for i in range(len(uniq))])
    med = np.median(r30[np.isfinite(r30) & (r30 < 9e8)])
    trades = []
    i = 31
    while i < len(uniq) - 1:
        if r30[i] < width_mult * med and \
                (hours is None or int(m_hour[i]) in hours):
            hi = mh[i - 30:i].max()
            lo = ml[i - 30:i].min()
            for k in range(i, min(i + 60, len(uniq) - 1)):
                d = 1 if mh[k] >= hi + brk else (-1 if ml[k] <= lo - brk else 0)
                if d:
                    pnl, jx = sim(m_sec0[k + 1], d, min(4.0, (hi - lo) + brk),
                                  trail_arm=2.0, trail_gb=1.2, timeout=3 * 3600)
                    trades.append((int(t[m_sec0[k]]), pnl))
                    i = np.searchsorted(m_sec0, jx)
                    break
            else:
                i += 30
        i += 1
    return trades


def cont15(move=3.0, pull=0.8, sl=2.5, hours=None):
    trades = []
    i = 16
    while i < len(uniq) - 35:
        mv = mc[i] - mc[i - 15]
        if abs(mv) >= move and (hours is None or int(m_hour[i]) in hours):
            d = 1 if mv > 0 else -1
            ext = mc[i]
            for k in range(i + 1, i + 30):
                ext = max(ext, mh[k]) if d > 0 else min(ext, ml[k])
                retr = (ext - ml[k]) if d > 0 else (mh[k] - ext)
                if retr >= pull:
                    pnl, jx = sim(m_sec0[k + 1], d, sl,
                                  trail_arm=2.0, trail_gb=1.2, timeout=2 * 3600)
                    trades.append((int(t[m_sec0[k]]), pnl))
                    i = np.searchsorted(m_sec0, jx)
                    break
            else:
                i += 15
        i += 1
    return trades


def exhaust(move=9.0, sl=4.0, tp=3.0, timeout=2700):
    trades = []
    i = 16
    while i < len(uniq) - 5:
        mv = mc[i] - mc[i - 15]
        if abs(mv) >= move:
            d = -1 if mv > 0 else 1
            pnl, jx = sim(m_sec0[i + 1], d, sl, tp=tp, timeout=timeout)
            trades.append((int(t[m_sec0[i]]), pnl))
            i = np.searchsorted(m_sec0, jx)
        i += 1
    return trades


if __name__ == "__main__":
    NIGHT = {20, 21, 0, 1, 2, 3, 4, 5}
    print("=== ORB (opening-range breakout) ===")
    report("ORB open=01     ", orb(1))
    report("ORB open=20     ", orb(20))
    print("=== SQUEEZE (compression breakout) ===")
    report("SQZ all-hours   ", squeeze())
    report("SQZ night       ", squeeze(hours=NIGHT))
    print("=== CONT15 (momentum + pullback entry) ===")
    report("C15 night       ", cont15(hours=NIGHT))
    report("C15 all         ", cont15())
    report("C15 night mv4   ", cont15(move=4.0, hours=NIGHT))
    print("=== EXHAUST (burst fade) ===")
    report("EXH mv9 tp3     ", exhaust())
    report("EXH mv12 tp4    ", exhaust(move=12.0, sl=5.0, tp=4.0))
    print("\nDONE movement_lab")
