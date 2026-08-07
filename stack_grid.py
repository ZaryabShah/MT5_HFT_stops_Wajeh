"""STACKED GRID (v4.9 candidate): v4.8 + pyramid rule — while a cycle is
purged-into-trend with profit >= arm*target and the gate still passes,
anchor an additional full grid at current price (max_stack cap).
Sweep arm {0.4, 0.6} x max_stack {2, 3} vs baseline; full period + halves."""
from datetime import datetime, timezone

import numpy as np

from backtest import adaptive_step, minute_ranges, raw_step
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)
t = secs["t"].astype(np.int64)
HOURS = {20, 21, 0, 1, 2, 3, 4, 5}
CFG = dict(step_mult=0.5, step_floor=0.30, step_cap=2.5)
LOT, C_, COMM = 0.01, 100.0, 0.0225
MID_SPLIT = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())


def new_grid(j, step):
    aa, ab = secs["ask_c"][j], secs["bid_c"][j]
    basis = LOT * C_ * step * 55 / 0.12
    return dict(
        buys=[round(aa + k * step, 3) for k in range(1, 12)],
        sells=[round(ab - k * step, 3) for k in range(1, 12)],
        longs=[], shorts=[], realized=0.0, peak=0.0, purged=False,
        target=basis * 0.12, maxloss=basis * 0.08)


def run(arm=None, max_stack=1, t_from=None, t_to=None):
    lo = np.searchsorted(t, t_from) if t_from else 0
    hi = np.searchsorted(t, t_to) if t_to else len(t)
    hour = (t // 3600) % 24
    equity = peak_eq = max_dd = 0.0
    ncyc = nwin = nstk = 0
    stk_pnl = 0.0
    grids = []
    idle_until = 0
    cur_day, day_pnl = -1, 0.0
    j = lo
    while j < hi:
        ts = int(t[j])
        ok_start = (ts >= idle_until and int(hour[j]) in HOURS and GATE[j]
                    and (secs["ask_c"][j] - secs["bid_c"][j]) <= 0.35
                    and raw_step(rng, ts, CFG)
                    >= 6.0 * (secs["ask_c"][j] - secs["bid_c"][j]))
        if not grids:
            if ok_start:
                grids.append(new_grid(j, adaptive_step(rng, ts, CFG)))
                grids[-1]["stacked"] = False
            j += 1
            continue
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        closed = []
        for g in grids:
            while g["buys"] and ah >= g["buys"][0]:
                g["longs"].append(max(g["buys"].pop(0), ao))
                g["realized"] -= COMM
            while g["sells"] and bl <= g["sells"][0]:
                g["shorts"].append(min(g["sells"].pop(0), bo))
                g["realized"] -= COMM
            profit = g["realized"] \
                + sum((bc - e) for e in g["longs"]) * C_ * LOT \
                + sum((e - ac) for e in g["shorts"]) * C_ * LOT
            g["peak"] = max(g["peak"], profit)
            out = None
            if profit >= g["target"]:
                out = "target"
            elif g["peak"] >= g["target"] * 0.5 and \
                    profit <= g["peak"] - g["target"] * 0.3:
                out = "trail"
            else:
                if not g["purged"]:
                    if len(g["longs"]) >= 5 and len(g["shorts"]) <= 2:
                        g["realized"] += sum((e - ac) for e in g["shorts"]) \
                            * C_ * LOT - COMM * len(g["shorts"])
                        g["shorts"], g["sells"], g["purged"] = [], [], True
                    elif len(g["shorts"]) >= 5 and len(g["longs"]) <= 2:
                        g["realized"] += sum((bc - e) for e in g["longs"]) \
                            * C_ * LOT - COMM * len(g["longs"])
                        g["longs"], g["buys"], g["purged"] = [], [], True
                if out is None and profit <= -g["maxloss"]:
                    out = "equitystop"
                elif out is None and min(len(g["longs"]),
                                         len(g["shorts"])) >= 3:
                    out = "paircap"
                elif out is None and not g["buys"] and not g["sells"] and \
                        (g["longs"] or g["shorts"]):
                    out = "all_filled"
            if out:
                pnl = g["realized"] \
                    + sum((bc - e) for e in g["longs"]) * C_ * LOT \
                    + sum((e - ac) for e in g["shorts"]) * C_ * LOT \
                    - COMM * (len(g["longs"]) + len(g["shorts"]))
                equity += pnl
                ncyc += 1
                nwin += pnl > 0
                if g["stacked"]:
                    nstk += 1
                    stk_pnl += pnl
                day = ts // 86400
                if day != cur_day:
                    cur_day, day_pnl = day, 0.0
                day_pnl += pnl
                if day_pnl <= -50:
                    idle_until = (day + 1) * 86400
                else:
                    idle_until = ts + 5
                peak_eq = max(peak_eq, equity)
                max_dd = min(max_dd, equity - peak_eq)
                closed.append(g)
        for g in closed:
            grids.remove(g)
        # pyramid spawn
        if arm and grids and len(grids) < max_stack and ok_start:
            lead = grids[0]
            profit0 = lead["realized"] \
                + sum((bc - e) for e in lead["longs"]) * C_ * LOT \
                + sum((e - ac) for e in lead["shorts"]) * C_ * LOT
            if lead["purged"] and profit0 >= arm * lead["target"]:
                g2 = new_grid(j, adaptive_step(rng, ts, CFG))
                g2["stacked"] = True
                grids.append(g2)
        j += 1
    return dict(net=equity, dd=max_dd, n=ncyc, w=nwin, nstk=nstk,
                stk=stk_pnl)


def show(label, r):
    nd = r["net"] / -r["dd"] if r["dd"] < 0 else float("inf")
    print(f"{label:<26}{r['net']:>+10.2f}{r['dd']:>+9.2f}{r['n']:>6}"
          f"{100 * r['w'] / max(r['n'], 1):>5.0f}%{nd:>6.1f}"
          f"{r['nstk']:>7}{r['stk']:>+10.2f}", flush=True)


if __name__ == "__main__":
    print(f"{'variant':<26}{'net':>10}{'maxDD':>9}{'cyc':>6}{'win%':>6}"
          f"{'n/DD':>6}{'stkcyc':>7}{'stk pnl':>10}")
    show("baseline (no stack)", run())
    best = None
    for arm in (0.4, 0.6):
        for ms in (2, 3):
            r = run(arm=arm, max_stack=ms)
            show(f"stack arm={arm} max={ms}", r)
            if best is None or r["net"] > best[2]["net"]:
                best = (arm, ms, r)
    arm, ms, _ = best
    print(f"\nhalves for best (arm={arm}, max={ms}) vs baseline:")
    for label, tf, tt in (("Apr-May", None, MID_SPLIT),
                          ("Jun-Jul", MID_SPLIT, None)):
        rb = run(t_from=tf, t_to=tt)
        rs = run(arm=arm, max_stack=ms, t_from=tf, t_to=tt)
        print(f"  {label}: baseline {rb['net']:+.2f} ({rb['dd']:+.2f}) | "
              f"stacked {rs['net']:+.2f} ({rs['dd']:+.2f})", flush=True)
    print("\nDONE stack_grid")
