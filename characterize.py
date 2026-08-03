"""Measure gold's behavior in the recorded 10 days:
1) continuation vs reversal: after a move of size X over horizon H, what does
   the NEXT H do on average?
2) volatility by hour of day (UTC) — when do trends live?
"""
import numpy as np

from backtest import build_seconds

secs = build_seconds()
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2

print("=== 1) momentum signature: E[next move | last move], sign-adjusted ===")
print("positive = continuation (momentum), negative = reversal (mean-rev)\n")
for h in (30, 60, 300, 900, 3600):
    tp = np.searchsorted(t, t - h)          # index of t-h
    tn = np.searchsorted(t, t + h)          # index of t+h
    ok = (tn < len(t)) & (t[np.clip(tn, 0, len(t) - 1)] == t + h) \
        & (t[tp] >= t - h - 2) & (np.arange(len(t)) > tp)
    idx = np.where(ok)[0][::h]              # non-overlapping samples
    prev = mid[idx] - mid[tp[idx]]
    nxt = mid[tn[idx]] - mid[idx]
    sign = np.sign(prev)
    adj = sign * nxt                        # + if continued, - if reversed
    q = np.quantile(np.abs(prev), [0.5, 0.8, 0.95])
    line = [f"h={h:>4}s (n={len(idx):,})"]
    for lo, hi, tag in [(0, q[0], "small"), (q[0], q[1], "mid"),
                        (q[1], q[2], "big"), (q[2], 1e9, "huge")]:
        m = (np.abs(prev) > lo) & (np.abs(prev) <= hi) & (sign != 0)
        if m.sum() > 20:
            cont = (adj[m] > 0).mean() * 100
            line.append(f"{tag}(|mv|>{lo:.2f}): {adj[m].mean():+.3f}$ {cont:.0f}%cont")
    print("  " + " | ".join(line))

print("\n=== 2) average 1-minute range by UTC hour ===")
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
bounds = np.append(idx, len(t))
ranges, hours = [], []
for i, m in enumerate(uniq):
    hi = secs["bid_h"][bounds[i]:bounds[i + 1]].max()
    lo = secs["bid_l"][bounds[i]:bounds[i + 1]].min()
    ranges.append(hi - lo)
    hours.append((m % 1440) // 60)
ranges = np.array(ranges)
hours = np.array(hours)
for hr in range(24):
    m = hours == hr
    if m.sum():
        print(f"  {hr:02d}:00 UTC  avg range ${ranges[m].mean():.2f}  "
              f"({'#' * int(ranges[m].mean() * 20)})")
