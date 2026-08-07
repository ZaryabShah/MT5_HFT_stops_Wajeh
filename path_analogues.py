"""EXPERIMENT 9 — HISTORICAL MICRO-PATH ANALOGUES (kNN). States on a 30s
grid: vol-normalized trailing mid moves over 10/30/60/180/600s + spread +
tick rate (7 dims, z-scored on train). Train = Apr-May: each state's outcome
= info-race mid +-$0.50 (no costs). Test = Jun-Jul: for each state find the
100 nearest TRAIN states (no temporal leakage — different months), p_hat =
mean neighbor outcome; trade only p_hat >= 0.62 / <= 0.38 with real costs.
NULL: same neighbors, outcomes shuffled, same thresholds."""
import numpy as np
from sklearn.neighbors import NearestNeighbors

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
mid = (bid + ask) / 2
spread = ask - bid
cnt10 = np.arange(n) - np.searchsorted(t, t - 10)
B = 0.5
rng = np.random.default_rng(7)

g_t = np.arange(int(t[0]) + 700, int(t[-1]), 30, dtype=np.int64)
gi = np.searchsorted(t, g_t, "right") - 1
fresh = (g_t - t[gi]) <= 30
gmid = mid[gi]
feats = []
for L in (10, 30, 60, 180, 600):
    gl = np.searchsorted(t, g_t - L, "right") - 1
    feats.append(gmid - mid[gl])
ch = np.diff(gmid, prepend=gmid[0])
c2 = np.cumsum(ch * ch)
vol = np.sqrt((c2 - np.concatenate([np.zeros(20), c2[:-20]])) / 20) + 1e-4
X = np.column_stack([f / vol for f in feats]
                    + [spread[gi] / 0.08, cnt10[gi] / 25.0])
valid = fresh & (g_t - t[0] > 700) & (spread[gi] <= 0.12)


def info_race(i):
    m0 = mid[i]
    up, dn = m0 + B, m0 - B
    j_end = np.searchsorted(t, t[i] + 1800, "right")
    j = i + 1
    while j < j_end:
        k = min(j_end, j + 8192)
        seg = mid[j:k]
        hit = (seg >= up) | (seg <= dn)
        if hit.any():
            return 1.0 if seg[int(np.argmax(hit))] >= up else 0.0
        j = k
    return np.nan


if __name__ == "__main__":
    tr = valid & (g_t < MID_SPLIT - 3600)
    te = valid & (g_t >= MID_SPLIT)
    tri = np.flatnonzero(tr)
    print(f"train states {len(tri)}  test states {int(te.sum())}",
          flush=True)
    y = np.array([info_race(int(gi[i])) for i in tri])
    ok = ~np.isnan(y)
    tri, y = tri[ok], y[ok]
    print(f"train outcomes {len(y)}  base P(up first) {y.mean():.3f}",
          flush=True)
    mu, sd = X[tri].mean(0), X[tri].std(0) + 1e-9
    nn = NearestNeighbors(n_neighbors=100).fit((X[tri] - mu) / sd)
    tei = np.flatnonzero(te)
    _, nb = nn.kneighbors((X[tei] - mu) / sd)
    ph = y[nb].mean(1)
    y_sh = rng.permutation(y)
    ph0 = y_sh[nb].mean(1)
    print(f"p_hat: min {ph.min():.3f} med {np.median(ph):.3f} "
          f"max {ph.max():.3f}")
    for th in (0.58, 0.62, 0.66):
        print(f"  |p-0.5|>={th-0.5:.2f}: real {(np.abs(ph-0.5)>=th-0.5).sum()}"
              f"  null {(np.abs(ph0-0.5)>=th-0.5).sum()}")
    header()
    for th in (0.58, 0.62):
        sig = np.zeros(n, np.int8)
        sel = np.abs(ph - 0.5) >= th - 0.5
        ii = gi[tei[sel]]
        sig[ii] = np.where(ph[sel] > 0.5, 1, -1).astype(np.int8)
        r = run_sim(t, bid, ask, sig, B)
        show(f"OOS th={th} B={B}", r)
        sig0 = np.zeros(n, np.int8)
        sel0 = np.abs(ph0 - 0.5) >= th - 0.5
        ii0 = gi[tei[sel0]]
        sig0[ii0] = np.where(ph0[sel0] > 0.5, 1, -1).astype(np.int8)
        show(f"NULL th={th} B={B}", run_sim(t, bid, ask, sig0, B))
    print("\nDONE path_analogues")
