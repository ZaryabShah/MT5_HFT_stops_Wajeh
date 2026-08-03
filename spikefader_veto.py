"""SpikeFader + volatility veto: no fade entries while |15-min move| > cap.
(Motivated by the pre-registered characterization: >$10/15min moves CONTINUE.)"""
from datetime import datetime, timezone

import numpy as np

from backtest import build_seconds
from strategies import precompute_move, respread


def run_veto(secs, mv60, mv900, f, tgt, stop, hold, veto, comm=0.0, lot=0.01):
    t = secs["t"]
    n = len(t)
    pos = 0
    entry = 0.0
    net = peak = maxdd = 0.0
    trades = wins = 0
    t_entry = 0
    for j in range(n):
        if pos == 0:
            if veto and abs(mv900[j]) > veto:
                continue
            m = mv60[j]
            if m >= f:
                pos, entry, t_entry = -1, secs["bid_c"][j], t[j]
                net -= comm * lot
            elif m <= -f:
                pos, entry, t_entry = 1, secs["ask_c"][j], t[j]
                net -= comm * lot
        elif pos == 1:
            hit_tp = secs["bid_h"][j] >= entry + tgt
            hit_sl = secs["bid_l"][j] <= entry - stop
            if hit_tp or hit_sl or t[j] - t_entry >= hold:
                fill = entry + tgt if hit_tp else (entry - stop if hit_sl else secs["bid_c"][j])
                pnl = (fill - entry) * 100 * lot - comm * lot
                net += pnl
                trades += 1
                wins += pnl > 0
                pos = 0
        else:
            hit_tp = secs["ask_l"][j] <= entry - tgt
            hit_sl = secs["ask_h"][j] >= entry + stop
            if hit_tp or hit_sl or t[j] - t_entry >= hold:
                fill = entry - tgt if hit_tp else (entry + stop if hit_sl else secs["ask_c"][j])
                pnl = (entry - fill) * 100 * lot - comm * lot
                net += pnl
                trades += 1
                wins += pnl > 0
                pos = 0
        peak = max(peak, net)
        maxdd = min(maxdd, net - peak)
    return net, trades, wins, maxdd


base = build_seconds()
fusion = respread(base, 0.031)
mv60 = precompute_move(fusion, 60)
mv900 = precompute_move(fusion, 900)
t = fusion["t"]

print("=== full 10 days, Fusion, F=3.5 tgt=1.0 stop=3.0 hold=300 ===")
for veto in (None, 10.0, 8.0, 6.0):
    net, tr, w, dd = run_veto(fusion, mv60, mv900, 3.5, 1.0, 3.0, 300,
                              veto, comm=2.25)
    print(f"veto {str(veto):>5}: net {net:+8.2f} | {tr:>4} trades | "
          f"{100*w/max(tr,1):.0f}% wins | maxDD {dd:+.2f}")

print("\n=== veto=8, daily ===")
days = np.unique(t // 86400)
for d in days:
    lo, hi = np.searchsorted(t, d * 86400), np.searchsorted(t, (d + 1) * 86400)
    if hi - lo < 1000:
        continue
    sub = {k: v[lo:hi] for k, v in fusion.items()}
    net, tr, w, dd = run_veto(sub, mv60[lo:hi], mv900[lo:hi], 3.5, 1.0, 3.0, 300,
                              8.0, comm=2.25)
    day = datetime.fromtimestamp(int(d * 86400), tz=timezone.utc).strftime("%a %m-%d")
    print(f"  {day}: net {net:+8.2f} | {tr:>3} trades | "
          f"{100*w/max(tr,1):.0f}% wins | maxDD {dd:+.2f}")
