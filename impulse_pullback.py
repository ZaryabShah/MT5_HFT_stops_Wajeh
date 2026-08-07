"""MOVE-START IMPULSE-PULLBACK (external research doc's #1 + #5 candidate):
at each v4.8 gate RISING EDGE (ER30>=0.25 & |move30|>=3 turning on = the
change-point / fresh-impulse moment), wait for a pullback of r*M against the
impulse (M = |30m move|), enter on resumption (+0.10*M bounce off the pullback
extreme), SL 0.10*M beyond the pullback extreme, TP at R multiples of risk.
Invalidate if retrace >0.65*M. Timeouts: arm 45m, pullback 30m, position 120m.
Sweep r x R x window; halves for best. Bid/ask execution, $2.25/side comm."""
from datetime import datetime, timezone

import numpy as np

from trend_gate import er_series, m_close, move_series, sec_minpos, secs

GATE = er_series(30, 0.25) & move_series(30, 3.0)
t = secs["t"].astype(np.int64)
hour = (t // 3600) % 24
mid_h = (secs["bid_h"] + secs["ask_h"]) / 2
mid_l = (secs["bid_l"] + secs["ask_l"]) / 2
V48 = {20, 21, 0, 1, 2, 3, 4, 5}
ALL = set(range(24))
COMM_RT = 0.045          # $ per 0.01-lot round trip
ARM_T, PULL_T, POS_T = 2700, 1800, 7200
RES_B, INV, SLB = 0.10, 0.65, 0.10
MID_SPLIT = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())

EDGES = np.flatnonzero(GATE[1:] & ~GATE[:-1]) + 1
pos = sec_minpos - 1
signed30 = m_close[np.clip(pos, 0, None)] - m_close[np.clip(pos - 30, 0, None)]


def first_true(mask):
    i = int(np.argmax(mask))
    return i if mask[i] else -1


def run(r_arm, rm, hours, t_from=None, t_to=None):
    trades = []
    n_edge = n_arm = n_ent = 0
    busy_until = 0
    for j0 in EDGES:
        ts0 = int(t[j0])
        if t_from and ts0 < t_from:
            continue
        if t_to and ts0 >= t_to:
            break
        if ts0 < busy_until or int(hour[j0]) not in hours:
            continue
        if secs["ask_c"][j0] - secs["bid_c"][j0] > 0.35:
            continue
        M = abs(float(signed30[j0]))
        d = 1 if signed30[j0] > 0 else -1
        n_edge += 1
        # ---- RIDE: wait for pullback of r_arm*M from post-edge extreme
        hi = np.searchsorted(t, ts0 + ARM_T)
        s = slice(j0, hi)
        if d > 0:
            ext = np.maximum.accumulate(mid_h[s])
            k = first_true(ext - mid_l[s] >= r_arm * M)
        else:
            ext = np.minimum.accumulate(mid_l[s])
            k = first_true(mid_h[s] - ext >= r_arm * M)
        if k < 0:
            busy_until = ts0 + ARM_T
            continue
        ja = j0 + k
        ext_v = float(ext[k])
        n_arm += 1
        # ---- PULL: enter on +RES_B*M resumption; invalidate at INV*M retrace
        hi2 = np.searchsorted(t, int(t[ja]) + PULL_T)
        s2 = slice(ja, hi2)
        if d > 0:
            pull = np.minimum.accumulate(mid_l[s2])
            trig = mid_h[s2] >= pull + RES_B * M
            inval = ext_v - pull > INV * M
        else:
            pull = np.maximum.accumulate(mid_h[s2])
            trig = mid_l[s2] <= pull - RES_B * M
            inval = pull - ext_v > INV * M
        k2 = first_true(trig | inval)
        if k2 < 0 or inval[k2]:
            busy_until = int(t[ja]) + PULL_T if k2 < 0 else int(t[ja + k2])
            continue
        je = ja + k2
        pull_v = float(pull[k2])
        n_ent += 1
        # ---- POSITION
        if d > 0:
            entry = float(secs["ask_c"][je])
            sl = pull_v - SLB * M
            risk = entry - sl
            tp = entry + rm * risk
        else:
            entry = float(secs["bid_c"][je])
            sl = pull_v + SLB * M
            risk = sl - entry
            tp = entry - rm * risk
        hi3 = np.searchsorted(t, int(t[je]) + POS_T)
        s3 = slice(je + 1, hi3)
        if d > 0:
            hit_sl = secs["bid_l"][s3] <= sl
            hit_tp = secs["bid_h"][s3] >= tp
        else:
            hit_sl = secs["ask_h"][s3] >= sl
            hit_tp = secs["ask_l"][s3] <= tp
        k3 = first_true(hit_sl | hit_tp)
        if k3 < 0:
            jx = hi3 - 1
            px = float(secs["bid_c"][jx] if d > 0 else secs["ask_c"][jx])
        else:
            jx = je + 1 + k3
            if hit_sl[k3]:                       # SL wins ties (conservative)
                px = min(sl, float(secs["bid_o"][jx])) if d > 0 \
                    else max(sl, float(secs["ask_o"][jx]))
            else:
                px = max(tp, float(secs["bid_o"][jx])) if d > 0 \
                    else min(tp, float(secs["ask_o"][jx]))
        pnl = (px - entry) * d * 100 * 0.01 - COMM_RT
        trades.append((int(t[jx]), pnl, pnl / max(risk, 1e-9)))
        busy_until = int(t[jx])
    eq = pk = dd = 0.0
    for _, p, _ in trades:
        eq += p
        pk = max(pk, eq)
        dd = min(dd, eq - pk)
    w = sum(1 for _, p, _ in trades if p > 0)
    return dict(net=eq, dd=dd, n=len(trades), w=w, edges=n_edge,
                armed=n_arm, avg_r=(np.mean([r for _, _, r in trades])
                                    if trades else 0.0))


def show(label, r):
    wr = 100 * r["w"] / max(r["n"], 1)
    print(f"{label:<26}{r['net']:>+9.2f}{r['dd']:>+9.2f}{r['n']:>6}{wr:>5.0f}%"
          f"{r['avg_r']:>+7.2f}{r['edges']:>7}{r['armed']:>6}", flush=True)


if __name__ == "__main__":
    print(f"{'config':<26}{'net':>9}{'maxDD':>9}{'trd':>6}{'win%':>6}"
          f"{'avgR':>7}{'edges':>7}{'armd':>6}")
    best = None
    for hours, hname in ((V48, "v48"), (ALL, "all")):
        for r_arm in (0.30, 0.40, 0.50):
            for rm in (1.5, 2.0, 3.0):
                r = run(r_arm, rm, hours)
                show(f"{hname} r={r_arm} R={rm}", r)
                if best is None or r["net"] > best[3]["net"]:
                    best = (hours, r_arm, rm, r)
    hours, r_arm, rm, _ = best
    hname = "v48" if hours is V48 else "all"
    print(f"\nhalves for best ({hname} r={r_arm} R={rm}):")
    a = run(r_arm, rm, hours, t_to=MID_SPLIT)
    b = run(r_arm, rm, hours, t_from=MID_SPLIT)
    print(f"  Apr-May: {a['net']:+.2f} ({a['dd']:+.2f}, {a['n']} trd) | "
          f"Jun-Jul: {b['net']:+.2f} ({b['dd']:+.2f}, {b['n']} trd)")
    print("\nDONE impulse_pullback")
