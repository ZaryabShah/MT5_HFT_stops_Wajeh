"""WAVE-1 CONDITION SCAN (user question: do A/B/C work in specific
conditions — low spread, high speed, particular sessions?). Frozen
mid-strength signals (no re-optimizing): A = N=50 X=0.5 imbalance,
B = k=3 m=0.2 efficiency, C = G=5s continuation. Each re-run inside six
condition slices, WITH the random-entry control re-run in the same slice
(the cost handicap changes with spread/speed, so signal must be judged
against its own slice's control, not the all-day one)."""
import numpy as np

from microlab import header, load, run_sim, show

t, bid, ask = load()
n = len(t)
hour = (t // 3600) % 24
spread = ask - bid
cnt10 = np.arange(n) - np.searchsorted(t, t - 10)
p60, p85 = np.percentile(cnt10, 60), np.percentile(cnt10, 85)
base_filt = (spread <= 0.12) & (cnt10 >= p60)

# --- A: quote-revision imbalance, N=50, X=0.5
db = np.diff(bid, prepend=bid[0])
da = np.diff(ask, prepend=ask[0])
up_ev = (db > 0).astype(np.int32) + (da > 0)
dn_ev = (db < 0).astype(np.int32) + (da < 0)
cu = np.cumsum(up_ev, dtype=np.int64)
cd = np.cumsum(dn_ev, dtype=np.int64)
N = 50
U = cu - np.concatenate([np.zeros(N, np.int64), cu[:-N]])
D = cd - np.concatenate([np.zeros(N, np.int64), cd[:-N]])
tot = U + D
imb = np.where(tot >= 12, (U - D) / np.maximum(tot, 1), 0.0)
imb[:N] = 0.0
sigA = np.zeros(n, np.int8)
sigA[imb >= 0.5] = 1
sigA[imb <= -0.5] = -1
sigA[~base_filt] = 0
del U, D, tot, imb

# --- B: impact efficiency, k=3, m=0.2
mid = (bid + ask) / 2
dm = np.diff(mid, prepend=mid[0])
cpos = np.cumsum(np.clip(dm, 0, None))
cneg = np.cumsum(np.clip(-dm, 0, None))
lo5 = np.searchsorted(t, t - 5)
upmove, dnmove = cpos - cpos[lo5], cneg - cneg[lo5]
upcnt, dncnt = cu - cu[lo5], cd - cd[lo5]
eff_up = upmove / np.maximum(upcnt, 1)
eff_dn = dnmove / np.maximum(dncnt, 1)
sigB = np.zeros(n, np.int8)
sigB[(eff_dn >= 3 * eff_up) & (dnmove >= 0.2) & (upcnt >= dncnt)] = -1
sigB[(eff_up >= 3 * eff_dn) & (upmove >= 0.2) & (dncnt >= upcnt)] = 1
sigB[~(base_filt & (upcnt + dncnt >= 20))] = 0
del cpos, cneg, upmove, dnmove, upcnt, dncnt, eff_up, eff_dn, lo5, cu, cd

# --- C: silence 5s -> 2s burst continuation
gap = np.diff(t, prepend=t[0])
cnt60 = np.arange(n) - np.searchsorted(t, t - 60)
sigC = np.zeros(n, np.int8)
for i in np.flatnonzero((gap >= 5) & (gap <= 600) & (cnt60 >= 30)):
    j2 = np.searchsorted(t, t[i] + 2, "right") - 1
    if j2 <= i or spread[j2] > 0.12:
        continue
    d = mid[j2] - mid[i - 1]
    if abs(d) >= 0.10:
        sigC[j2] = 1 if d > 0 else -1

# --- control: stride entries through the same base filter
sigX = np.zeros(n, np.int8)
stride = np.arange(2000, n, 2000)
sigX[stride[::2]] = 1
sigX[stride[1::2]] = -1
sigX[~base_filt] = 0

V48 = np.isin(hour, (20, 21, 0, 1, 2, 3, 4, 5))
CONDS = [
    ("allday", np.ones(n, bool)),
    ("v48win", V48),
    ("day08-19", (hour >= 8) & (hour <= 19)),
    ("spr<=.08", spread <= 0.08),
    ("fast p85", cnt10 >= p85),
    ("v48+tight", V48 & (spread <= 0.08)),
]
SIGS = [("CTRL", sigX), ("A-imb", sigA), ("B-eff", sigB), ("C-sil", sigC)]

if __name__ == "__main__":
    header()
    for cname, mask in CONDS:
        for sname, sig in SIGS:
            s = np.where(mask, sig, 0).astype(np.int8)
            for B in (0.5, 1.0):
                show(f"{cname:<10}{sname} B={B}",
                     run_sim(t, bid, ask, s, B))
        print(flush=True)
    print("DONE cond_scan")
