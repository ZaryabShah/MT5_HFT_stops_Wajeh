"""US-SESSION LAB (user mandate 08-06): strategies FOR the fast-reverting
US tape, built from measured physics. Real Fusion feed, 4 months.
  SF   SpikeFader (the shelved survivor): fade |60s move| >= T, small TP,
       hard SL, short hold. Variants: threshold, spread-normalized entry.
  RF   RangeFade: fade touches of the rolling 60-min range edge when the
       range is wide (whipsaw thrash between edges is the payer).
  MR   MeanRevert: fade deviations >= D from the 45-min mean, target mean.
  MM   MicroMomentum: follow 30s impulses for a quick TP before the revert.
IS = Apr-May (tuning), OOS = Jun-Jul (untouched judge). Real bid/ask + comm.
US hours = server 15-20 unless stated."""
from datetime import datetime, timezone

import numpy as np

from trend_gate import secs

CONTRACT, LOT, COMM_RT = 100.0, 0.01, 0.045
t = secs["t"].astype(np.int64)
n = len(t)
bid_c, ask_c = secs["bid_c"], secs["ask_c"]
mid = (bid_c + ask_c) / 2
spread = ask_c - bid_c
hour = (t // 3600) % 24
JUN1 = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
US = {15, 16, 17, 18, 19}

# 60s and 30s lagged mid (by TIME, not index — data has gaps)
lag60 = np.searchsorted(t, t - 60, side="right") - 1
lag30 = np.searchsorted(t, t - 30, side="right") - 1
ok60 = (t - t[lag60]) <= 90
ok30 = (t - t[lag30]) <= 45
mv60 = np.where(ok60, mid - mid[np.clip(lag60, 0, None)], 0.0)
mv30 = np.where(ok30, mid - mid[np.clip(lag30, 0, None)], 0.0)

# minute closes for range/mean structures
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
b = np.append(idx, n)
mcl = mid[b[1:] - 1]
mhi = np.array([mid[b[i]:b[i + 1]].max() for i in range(len(uniq))])
mlo = np.array([mid[b[i]:b[i + 1]].min() for i in range(len(uniq))])
sec_min = np.searchsorted(uniq, mins)


def sim(i0, d, sl, tp, timeout):
    entry = ask_c[i0] if d > 0 else bid_c[i0]
    j = i0 + 1
    while j < n and t[j] - t[i0] < timeout:
        if d > 0:
            if secs["bid_l"][j] <= entry - sl:
                return (-sl * CONTRACT * LOT - COMM_RT, j)
            if secs["bid_h"][j] >= entry + tp:
                return (tp * CONTRACT * LOT - COMM_RT, j)
        else:
            if secs["ask_h"][j] >= entry + sl:
                return (-sl * CONTRACT * LOT - COMM_RT, j)
            if secs["ask_l"][j] <= entry - tp:
                return (tp * CONTRACT * LOT - COMM_RT, j)
        j += 1
    j = min(j, n - 1)
    pnl = (bid_c[j] - entry) if d > 0 else (entry - ask_c[j])
    return (pnl * CONTRACT * LOT - COMM_RT, j)


def report(name, trades):
    line = f"  {name}:"
    for half, f in (("IS ", lambda x: x < JUN1), ("OOS", lambda x: x >= JUN1)):
        sub = [p for ts, p in trades if f(ts)]
        if not sub:
            line += f"  {half} no trades"
            continue
        w = sum(1 for p in sub if p > 0)
        eq = np.cumsum(sub)
        dd = float(np.min(eq - np.maximum.accumulate(eq))) if len(sub) else 0
        line += (f"  {half} {sum(sub):>+8.2f} ({len(sub):>4}tr "
                 f"{100 * w / len(sub):>3.0f}% dd{dd:>+7.2f})")
    print(line, flush=True)


def spikefader(thresh, tp, sl, hold, hours, max_spread=None, cooldown=30):
    trades = []
    i = 1
    while i < n - 2:
        if int(hour[i]) in hours and abs(mv60[i]) >= thresh:
            if max_spread is None or spread[i] <= max_spread:
                d = -1 if mv60[i] > 0 else 1
                pnl, j = sim(i + 1, d, sl, tp, hold)
                trades.append((int(t[i]), pnl))
                i = j + cooldown
                continue
        i += 1
    return trades


def rangefade(width_min, tp, sl, hours):
    trades = []
    i = 61
    while i < len(uniq) - 2:
        if int((uniq[i] * 60 // 3600) % 24) in hours:
            hi = mhi[i - 60:i].max()
            lo = mlo[i - 60:i].min()
            if hi - lo >= width_min:
                d = 0
                if mhi[i] >= hi:
                    d = -1
                elif mlo[i] <= lo:
                    d = 1
                if d:
                    s0 = b[i + 1] - 1
                    pnl, j = sim(s0, d, sl, min(tp, (hi - lo) / 2), 2700)
                    trades.append((int(t[s0]), pnl))
                    i = sec_min[min(j, n - 1)] + 5
                    continue
        i += 1
    return trades


def meanrev(dev, tp, sl, hours):
    trades = []
    i = 46
    while i < len(uniq) - 2:
        if int((uniq[i] * 60 // 3600) % 24) in hours:
            m = mcl[i - 45:i].mean()
            d0 = mcl[i] - m
            if abs(d0) >= dev:
                d = -1 if d0 > 0 else 1
                s0 = b[i + 1] - 1
                pnl, j = sim(s0, d, sl, tp, 2700)
                trades.append((int(t[s0]), pnl))
                i = sec_min[min(j, n - 1)] + 5
                continue
        i += 1
    return trades


def micromom(thresh, tp, sl, hold, hours, cooldown=60):
    trades = []
    i = 1
    while i < n - 2:
        if int(hour[i]) in hours and abs(mv30[i]) >= thresh:
            d = 1 if mv30[i] > 0 else -1
            pnl, j = sim(i + 1, d, sl, tp, hold)
            trades.append((int(t[i]), pnl))
            i = j + cooldown
            continue
        i += 1
    return trades


if __name__ == "__main__":
    print("=== SF SpikeFader (the shelved survivor, on REAL 4mo feed) ===")
    report("SF t3.5 tp1.0 sl3 US   ", spikefader(3.5, 1.0, 3.0, 300, US))
    report("SF t4.5 tp1.0 sl3 US   ", spikefader(4.5, 1.0, 3.0, 300, US))
    report("SF t3.5 tp1.5 sl3 US   ", spikefader(3.5, 1.5, 3.0, 300, US))
    report("SF t3.5 tp1 sl3 US spr ", spikefader(3.5, 1.0, 3.0, 300, US,
                                                 max_spread=0.10))
    report("SF t3.5 tp1 sl3 ALLDAY ", spikefader(3.5, 1.0, 3.0, 300,
                                                 set(range(24))))
    print("=== RF RangeFade (60-min range edges) ===")
    report("RF w4 tp2 sl2.5 US     ", rangefade(4.0, 2.0, 2.5, US))
    report("RF w6 tp2.5 sl3 US     ", rangefade(6.0, 2.5, 3.0, US))
    print("=== MR MeanRevert (45-min mean) ===")
    report("MR d4 tp1.8 sl3 US     ", meanrev(4.0, 1.8, 3.0, US))
    report("MR d5.5 tp2.2 sl3.5 US ", meanrev(5.5, 2.2, 3.5, US))
    print("=== MM MicroMomentum (follow 30s impulse) ===")
    report("MM t1.8 tp1 sl1.8 US   ", micromom(1.8, 1.0, 1.8, 120, US))
    report("MM t2.5 tp1.2 sl2 US   ", micromom(2.5, 1.2, 2.0, 120, US))
    print("\nDONE uslab")
