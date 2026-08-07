"""EXPERIMENT A — BID/ASK REVISION PRESSURE. Per tick score up/down quote
revisions (bid-up + ask-up vs bid-down + ask-down), rolling N-tick imbalance
(U-D)/(U+D); long when imb >= X, short when <= -X, under spread <= $0.12 and
tick-rate >= 60th pct. Barrier race +-B. Control = unconditional stride
signals with the same filters (measures the baseline cost handicap)."""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
db = np.diff(bid, prepend=bid[0])
da = np.diff(ask, prepend=ask[0])
up_ev = (db > 0).astype(np.int32) + (da > 0)
dn_ev = (db < 0).astype(np.int32) + (da < 0)
cu = np.cumsum(up_ev, dtype=np.int64)
cd = np.cumsum(dn_ev, dtype=np.int64)
spread_ok = (ask - bid) <= 0.12
cnt10 = np.arange(n) - np.searchsorted(t, t - 10)
rate_ok = cnt10 >= np.percentile(cnt10, 60)
filt = spread_ok & rate_ok


def imbalance(N):
    U = cu - np.concatenate([np.zeros(N, np.int64), cu[:-N]])
    D = cd - np.concatenate([np.zeros(N, np.int64), cd[:-N]])
    tot = U + D
    imb = np.where(tot >= max(10, N // 4), (U - D) / np.maximum(tot, 1), 0.0)
    imb[:N] = 0.0
    return imb


if __name__ == "__main__":
    header()
    ctrl = np.zeros(n, np.int8)
    stride = np.arange(2000, n, 2000)
    ctrl[stride[::2]] = 1
    ctrl[stride[1::2]] = -1
    ctrl[~filt] = 0
    for B in (0.5, 1.0):
        show(f"CONTROL stride B={B}", run_sim(t, bid, ask, ctrl, B))
    best = None
    for N in (50, 100):
        imb = imbalance(N)
        for X in (0.4, 0.5, 0.6):
            sig = np.zeros(n, np.int8)
            sig[imb >= X] = 1
            sig[imb <= -X] = -1
            sig[~filt] = 0
            for B in (0.5, 1.0):
                r = run_sim(t, bid, ask, sig, B)
                show(f"N={N} X={X} B={B}", r)
                if best is None or r["net"] > best[3]["net"]:
                    best = (N, X, B, r)
    N, X, B, _ = best
    print(f"\nhalves for best (N={N} X={X} B={B}):")
    imb = imbalance(N)
    sig = np.zeros(n, np.int8)
    sig[imb >= X] = 1
    sig[imb <= -X] = -1
    sig[~filt] = 0
    a = run_sim(t, bid, ask, sig, B, t_to=MID_SPLIT)
    b = run_sim(t, bid, ask, sig, B, t_from=MID_SPLIT)
    print(f"  Apr-May: {a['net']:+.2f} ({a['n']} trd, {a['wres']:.1f}%) | "
          f"Jun-Jul: {b['net']:+.2f} ({b['n']} trd, {b['wres']:.1f}%)")
    print("\nDONE quote_pressure")
