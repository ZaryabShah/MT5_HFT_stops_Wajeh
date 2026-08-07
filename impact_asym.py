"""EXPERIMENT B — LIQUIDITY IMPACT ASYMMETRY. Trailing 5s window: how many
$ did price move per up-revision vs per down-revision? Trade TOWARD the more
efficient side (the side that moves price with LESS pressure = less
resistance), requiring the efficient side to have moved >= m dollars and the
INEFFICIENT side to have thrown >= as many revisions (pressure that failed).
eff ratio >= k. Same filters/race as experiment A."""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
mid = (bid + ask) / 2
dm = np.diff(mid, prepend=mid[0])
db = np.diff(bid, prepend=bid[0])
da = np.diff(ask, prepend=ask[0])
up_ev = (db > 0).astype(np.int32) + (da > 0)
dn_ev = (db < 0).astype(np.int32) + (da < 0)
cpos = np.cumsum(np.clip(dm, 0, None))
cneg = np.cumsum(np.clip(-dm, 0, None))
cu = np.cumsum(up_ev, dtype=np.int64)
cd = np.cumsum(dn_ev, dtype=np.int64)
lo5 = np.searchsorted(t, t - 5)


def win(c):
    return c - c[lo5]


upmove, dnmove = win(cpos), win(cneg)
upcnt, dncnt = win(cu), win(cd)
eff_up = upmove / np.maximum(upcnt, 1)
eff_dn = dnmove / np.maximum(dncnt, 1)
spread_ok = (ask - bid) <= 0.12
cnt10 = np.arange(n) - np.searchsorted(t, t - 10)
rate_ok = cnt10 >= np.percentile(cnt10, 60)
filt = spread_ok & rate_ok & (upcnt + dncnt >= 20)


def signals(k, m):
    sig = np.zeros(n, np.int8)
    sig[(eff_dn >= k * eff_up) & (dnmove >= m) & (upcnt >= dncnt)] = -1
    sig[(eff_up >= k * eff_dn) & (upmove >= m) & (dncnt >= upcnt)] = 1
    sig[~filt] = 0
    return sig


if __name__ == "__main__":
    header()
    best = None
    for k in (2, 3, 5):
        for m in (0.2, 0.4):
            sig = signals(k, m)
            for B in (0.5, 1.0):
                r = run_sim(t, bid, ask, sig, B)
                show(f"k={k} m={m} B={B}", r)
                if best is None or r["net"] > best[3]["net"]:
                    best = (k, m, B, r)
    k, m, B, _ = best
    print(f"\nhalves for best (k={k} m={m} B={B}):")
    sig = signals(k, m)
    a = run_sim(t, bid, ask, sig, B, t_to=MID_SPLIT)
    b = run_sim(t, bid, ask, sig, B, t_from=MID_SPLIT)
    print(f"  Apr-May: {a['net']:+.2f} ({a['n']} trd, {a['wres']:.1f}%) | "
          f"Jun-Jul: {b['net']:+.2f} ({b['n']} trd, {b['wres']:.1f}%)")
    print("\nDONE impact_asym")
