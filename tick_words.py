"""EXPERIMENT 8 — TICK-WORD / ENTROPY PREDICTOR. Symbols per tick:
0=mid up+spread not expanding, 1=mid up+expanding, 2=down+not expanding,
3=down+expanding, 4=no change. Words = last 5 symbols (5^5=3125 codes).
IS (Apr-May): for each frequent word, sample up to 400 occurrences and race
mid +-$0.50 (no costs — pure information); NULL calibration = 30 random
pseudo-words (sampling noise sd ~ 0.025). Select words with p>=0.60 or
<=0.40 (4 sigma AND past the cost bar). OOS (Jun-Jul): trade the frozen
selection with real costs. No selection = distribution report + falsified."""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
mid = (bid + ask) / 2
spread = ask - bid
dm = np.diff(mid, prepend=mid[0])
ds = np.diff(spread, prepend=spread[0])
s = np.select([(dm > 0) & (ds <= 0), (dm > 0) & (ds > 0),
               (dm < 0) & (ds <= 0), (dm < 0) & (ds > 0)],
              [0, 1, 2, 3], default=4).astype(np.int16)
code = s.copy()
for k, w in ((1, 5), (2, 25), (3, 125), (4, 625)):
    code[k:] += w * s[:-k]
code[:4] = -1
TRAIN_END = MID_SPLIT - 3600
B = 0.5
rng = np.random.default_rng(7)


def info_race(i):
    m0 = mid[i]
    up, dn = m0 + B, m0 - B
    ts_end = t[i] + 1800
    j_end = np.searchsorted(t, ts_end, "right")
    j = i + 1
    while j < j_end:
        k = min(j_end, j + 8192)
        seg = mid[j:k]
        hit = (seg >= up) | (seg <= dn)
        if hit.any():
            return 1 if seg[int(np.argmax(hit))] >= up else 0
        j = k
    return -1


def sample_p(occ, cap=400):
    if len(occ) > cap:
        occ = occ[:: len(occ) // cap][:cap]
    res = [info_race(int(i)) for i in occ]
    res = [r for r in res if r >= 0]
    return (np.mean(res) if res else 0.5), len(res)


if __name__ == "__main__":
    train = np.flatnonzero((t < TRAIN_END) & (code >= 0))
    cnt = np.bincount(code[train], minlength=3125)
    top = np.argsort(cnt)[::-1]
    top = top[cnt[top] >= 2000][:300]
    occ_by = {int(c): train[code[train] == c] for c in top}
    ps = {}
    for c in top:
        p, m = sample_p(occ_by[int(c)])
        ps[int(c)] = (p, m)
    arr = np.array([p for p, _ in ps.values()])
    null = [sample_p(np.sort(rng.choice(train, 400, replace=False)))[0]
            for _ in range(30)]
    nd = np.abs(np.array(null) - 0.5)
    print(f"words={len(arr)}  p: min {arr.min():.3f}  med "
          f"{np.median(arr):.3f}  max {arr.max():.3f}")
    print(f"|p-0.5|>=0.06: {(np.abs(arr-0.5)>=0.06).sum()}  >=0.10: "
          f"{(np.abs(arr-0.5)>=0.10).sum()}")
    print(f"NULL 30 pseudo-words: max|p-0.5| {nd.max():.3f}  "
          f"med {np.median(nd):.3f}", flush=True)
    sel = {c: (1 if p > 0.5 else -1) for c, (p, m) in ps.items()
           if abs(p - 0.5) >= 0.10 and m >= 200}
    print(f"selected words: {len(sel)}")
    if sel:
        header()
        sig = np.zeros(n, np.int8)
        for c, d in sel.items():
            sig[(code == c) & (t >= MID_SPLIT)] = d
        sig[spread > 0.12] = 0
        for Bx in (0.5, 1.0):
            show(f"OOS Jun-Jul {len(sel)} words B={Bx}",
                 run_sim(t, bid, ask, sig, Bx))
    else:
        print("no word cleared 0.10 — FALSIFIED at selection stage")
    print("\nDONE tick_words")
