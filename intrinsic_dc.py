"""EXPERIMENT 4 — INTRINSIC-TIME DIRECTIONAL CHANGES. Clock time discarded:
a DC event fires when mid reverses theta dollars from the running extreme.
At each DC confirmation, trade the NEW direction (cont = bet on overshoot)
or against it (fade). Then condition the best variant on the ending run's
overshoot (small/large vs 0.5*theta) and its duration (fast/slow vs median).
Barrier race with real costs as in wave 1."""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
mid = (bid + ask) / 2
spread_ok = (ask - bid) <= 0.12
CH = 262144


def dc_events(theta):
    """Chunked vectorized DC walk. Returns (idx, dir, prev_os, prev_dur)."""
    idx, drc, pos, pdu = [], [], [], []
    i, mode, ext = 1, 1, float(mid[0])
    conf_p, conf_t = None, None
    while i < n:
        j = min(n, i + CH)
        seg = mid[i:j]
        if mode > 0:
            cm = np.maximum.accumulate(np.concatenate(([ext], seg)))[1:]
            hit = cm - seg >= theta
        else:
            cm = np.minimum.accumulate(np.concatenate(([ext], seg)))[1:]
            hit = seg - cm >= theta
        k = int(np.argmax(hit)) if hit.any() else -1
        if k < 0:
            ext = float(cm[-1])
            i = j
            continue
        c = i + k
        idx.append(c)
        drc.append(-mode)
        pos.append(float(abs(cm[k] - conf_p)) if conf_p is not None
                   else np.nan)
        pdu.append(float(t[c] - conf_t) if conf_t is not None else np.nan)
        mode = -mode
        ext = float(mid[c])
        conf_p, conf_t = float(mid[c]), int(t[c])
        i = c + 1
    return (np.array(idx[2:]), np.array(drc[2:], np.int8),
            np.array(pos[2:]), np.array(pdu[2:]))


def sig_from(idx, d, sel=None):
    sig = np.zeros(n, np.int8)
    m = np.ones(len(idx), bool) if sel is None else sel
    ii = idx[m]
    sig[ii] = d[m]
    sig[~spread_ok] = 0
    return sig


if __name__ == "__main__":
    header()
    ev = {}
    best = None
    for theta in (0.5, 1.0, 2.0):
        idx, d, pos, pdu = dc_events(theta)
        ev[theta] = (idx, d, pos, pdu)
        for mode, dd in (("cont", d), ("fade", -d)):
            sig = sig_from(idx, dd)
            for B in (0.5, 1.0):
                r = run_sim(t, bid, ask, sig, B)
                show(f"th={theta} {mode} B={B} (dc={len(idx)})", r)
                if best is None or r["net"] > best[4]["net"]:
                    best = (theta, mode, B, dd, r)
    theta, mode, B, dd, _ = best
    idx, d, pos, pdu = ev[theta]
    dd = d if mode == "cont" else -d
    md = np.nanmedian(pdu)
    print(f"\nconditioned splits of best (th={theta} {mode} B={B}, "
          f"median dur={md:.0f}s):")
    for lbl, sel in (("prev_os<0.5th", pos < 0.5 * theta),
                     ("prev_os>=0.5th", pos >= 0.5 * theta),
                     (f"fast dur", pdu < md), (f"slow dur", pdu >= md),
                     ("os<0.5th & fast", (pos < 0.5 * theta) & (pdu < md))):
        show(f"  {lbl}", run_sim(t, bid, ask, sig_from(idx, dd, sel), B))
    a = run_sim(t, bid, ask, sig_from(idx, dd), B, t_to=MID_SPLIT)
    b = run_sim(t, bid, ask, sig_from(idx, dd), B, t_from=MID_SPLIT)
    print(f"halves: Apr-May {a['net']:+.2f} ({a['n']}) | "
          f"Jun-Jul {b['net']:+.2f} ({b['n']})")
    print("\nDONE intrinsic_dc")
