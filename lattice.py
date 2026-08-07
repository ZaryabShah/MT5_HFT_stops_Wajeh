"""EXPERIMENT 5 — PRICE-LATTICE STATE MACHINE. Round-number behavior:
levels = multiples of $1 / $5 / $10. A touch = mid entering the +-$0.10 band
around the nearest level; touches are ranked within an episode (episode =
while that level stays nearest). At the k-th touch, arriving from below/above,
trade BREAK (through the level) or REJECT (bounce). Barrier race, real costs.
(The $0.25 lattice is untestable: its +-0.10 bands cover 80% of price space.)"""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
mid = (bid + ask) / 2
spread_ok = (ask - bid) <= 0.12


def touches(L):
    lev = np.round(mid / L) * L
    dist = mid - lev
    inb = np.abs(dist) <= 0.10
    new_ep = np.diff(lev, prepend=lev[0]) != 0
    eid = np.cumsum(new_ep)
    entry = inb & ~np.roll(inb, 1)
    entry[0] = False
    idx = np.flatnonzero(entry)
    idx = idx[idx > 0]
    d = np.where(dist[idx - 1] < 0, 1, -1).astype(np.int8)  # from below=+1
    et = eid[idx]
    uniq, first = np.unique(et, return_index=True)
    rank = np.arange(len(idx)) - first[np.searchsorted(uniq, et)]
    return idx, d, rank


if __name__ == "__main__":
    header()
    for L in (1.0, 5.0, 10.0):
        idx, d, rank = touches(L)
        for rlbl, rsel in (("1st", rank == 0), ("2nd", rank == 1),
                           ("3rd+", rank >= 2)):
            for mode in ("break", "reject"):
                sig = np.zeros(n, np.int8)
                ii = idx[rsel]
                sig[ii] = d[rsel] if mode == "break" else -d[rsel]
                sig[~spread_ok] = 0
                r = run_sim(t, bid, ask, sig, 0.5)
                show(f"L={L:>4} {rlbl:<4} {mode} B=0.5", r)
        print(flush=True)
    print("DONE lattice")
