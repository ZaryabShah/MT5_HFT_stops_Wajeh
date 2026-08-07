"""Shared machinery for the tick-microstructure experiment series (quote
pressure / impact asymmetry / silence-burst). Raw tick arrays + a barrier-race
simulator: enter at market (long=ask, short=bid), race +-B measured on the
exit side (long exits on bid, short on ask), quote-touch with gap-through,
$2.25/side/lot commission, 30-min timeout -> mark out. Sequential, one race
at a time (cooldown = race duration), so results are directly tradable."""
import os
from datetime import datetime, timezone

import numpy as np

RAW = "data/ticks_fusion.npz"
CACHE = "data/ticks_raw_cache.npz"
COMM_RT = 0.045
TIMEOUT = 1800
MID_SPLIT = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())


def load():
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        return z["t"], z["bid"], z["ask"]
    ticks = np.load(RAW)["ticks"]
    t = ticks["time"].astype(np.int64)
    bid = ticks["bid"].astype(np.float64)
    ask = ticks["ask"].astype(np.float64)
    np.savez(CACHE, t=t, bid=bid, ask=ask)
    return t, bid, ask


def run_sim(t, bid, ask, sig_dir, barrier, t_from=None, t_to=None,
            chunk=8192):
    """sig_dir: int8 per tick (+1 long / -1 short / 0). Returns stats dict."""
    n = len(t)
    idxs = np.flatnonzero(sig_dir != 0)
    if t_from:
        idxs = idxs[t[idxs] >= t_from]
    if t_to:
        idxs = idxs[t[idxs] < t_to]
    trades = []
    eq = pk = dd = 0.0
    nw = nto = 0
    ptr = 0
    cool = 0
    while ptr < len(idxs):
        i = int(idxs[ptr])
        if i <= cool:
            ptr += 1
            continue
        d = int(sig_dir[i])
        if d > 0:
            entry = ask[i]
            side = bid
            up, dn = entry + barrier, entry - barrier
        else:
            entry = bid[i]
            side = ask
            up, dn = entry + barrier, entry - barrier
        ts_end = t[i] + TIMEOUT
        j_end = np.searchsorted(t, ts_end, "right")
        j = i + 1
        jx, px, out = -1, 0.0, 0
        while j < min(n, j_end):
            k = min(j_end, j + chunk, n)
            seg = side[j:k]
            hit = (seg >= up) | (seg <= dn)
            if hit.any():
                m = int(np.argmax(hit))
                jx = j + m
                px = float(seg[m])
                out = 1 if (d > 0) == (px >= up) else -1
                break
            j = k
        if jx < 0:
            jx = min(j_end, n) - 1
            px = float(side[jx])
            out = 0
            nto += 1
        pnl = (px - entry) * d - COMM_RT
        trades.append(pnl)
        nw += pnl > 0
        eq += pnl
        pk = max(pk, eq)
        dd = min(dd, eq - pk)
        cool = jx
        ptr = np.searchsorted(idxs, jx + 1)
    nres = len(trades) - nto
    return dict(net=eq, dd=dd, n=len(trades), w=nw, nto=nto,
                wres=(100 * nw / nres if nres else 0.0),
                avg=(eq / len(trades) if trades else 0.0))


def show(label, r):
    print(f"{label:<28}{r['net']:>+9.2f}{r['dd']:>+9.2f}{r['n']:>7}"
          f"{r['wres']:>6.1f}%{r['nto']:>6}{r['avg']:>+8.3f}", flush=True)


def header():
    print(f"{'config':<28}{'net':>9}{'maxDD':>9}{'trades':>7}{'win%':>7}"
          f"{'t/o':>6}{'avg$':>8}")
