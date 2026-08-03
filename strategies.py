"""Data-driven strategy candidates, tuned in-sample (Jul 20-28) and validated
out-of-sample (Jul 29-31), under both cost models.

S1 TrendRider: enter on moderate 15-min momentum (excluding overextension),
   trail out. Exploits the measured +0.84$/57% continuation bucket.
S2 SpikeFader: fade 1-min spikes >= F, small target, hard stop, max hold.
   Exploits the measured second-scale reversion.
"""
import numpy as np

from backtest import build_seconds

from datetime import datetime, timezone

OOS_SPLIT = int(datetime(2026, 7, 29, tzinfo=timezone.utc).timestamp())


def respread(secs, half):
    out = dict(t=secs["t"])
    for f in ("o", "h", "l", "c"):
        m = (secs[f"bid_{f}"] + secs[f"ask_{f}"]) / 2
        out[f"bid_{f}"] = m - half
        out[f"ask_{f}"] = m + half
    return out


def precompute_move(secs, lookback):
    t = secs["t"].astype(np.int64)
    mid = (secs["bid_c"] + secs["ask_c"]) / 2
    prev = np.searchsorted(t, t - lookback)
    move = mid - mid[prev]
    ok = (t - t[prev]) <= lookback + 120     # tolerate small gaps
    move[~ok] = 0.0
    return move


def run_trendrider(secs, move, t1, t2, trail, comm=0.0, lot=0.01, cooldown=300):
    t = secs["t"]
    n = len(t)
    pos = 0
    entry = sl = 0.0
    net = peak = maxdd = 0.0
    trades = wins = 0
    wait_until = 0
    j = 0
    while j < n:
        if pos == 0:
            if t[j] >= wait_until:
                m = move[j]
                if t1 <= m <= t2:
                    pos, entry = 1, secs["ask_c"][j]
                    sl = entry - trail
                    net -= comm * lot
                elif -t2 <= m <= -t1:
                    pos, entry = -1, secs["bid_c"][j]
                    sl = entry + trail
                    net -= comm * lot
        elif pos == 1:
            sl = max(sl, secs["bid_h"][j] - trail)
            if secs["bid_l"][j] <= sl:
                fill = min(sl, secs["bid_o"][j])
                pnl = (fill - entry) * 100 * lot - comm * lot
                net += pnl
                trades += 1
                wins += pnl > 0
                pos = 0
                wait_until = t[j] + cooldown
        else:
            sl = min(sl, secs["ask_l"][j] + trail)
            if secs["ask_h"][j] >= sl:
                fill = max(sl, secs["ask_o"][j])
                pnl = (entry - fill) * 100 * lot - comm * lot
                net += pnl
                trades += 1
                wins += pnl > 0
                pos = 0
                wait_until = t[j] + cooldown
        peak = max(peak, net)
        maxdd = min(maxdd, net - peak)
        j += 1
    return net, trades, wins, maxdd


def run_spikefader(secs, move, f, target, stop, maxhold, comm=0.0, lot=0.01):
    t = secs["t"]
    n = len(t)
    pos = 0
    entry = 0.0
    net = peak = maxdd = 0.0
    trades = wins = 0
    t_entry = 0
    j = 0
    while j < n:
        if pos == 0:
            m = move[j]
            if m >= f:                       # spike up -> fade short
                pos, entry, t_entry = -1, secs["bid_c"][j], t[j]
                net -= comm * lot
            elif m <= -f:                    # spike down -> fade long
                pos, entry, t_entry = 1, secs["ask_c"][j], t[j]
                net -= comm * lot
        else:
            if pos == 1:
                hit_tp = secs["bid_h"][j] >= entry + target
                hit_sl = secs["bid_l"][j] <= entry - stop
                fill = entry + target if hit_tp else entry - stop
                if hit_tp or hit_sl or t[j] - t_entry >= maxhold:
                    if not (hit_tp or hit_sl):
                        fill = secs["bid_c"][j]
                    pnl = (fill - entry) * 100 * lot - comm * lot
                    net += pnl
                    trades += 1
                    wins += pnl > 0
                    pos = 0
            else:
                hit_tp = secs["ask_l"][j] <= entry - target
                hit_sl = secs["ask_h"][j] >= entry + stop
                fill = entry - target if hit_tp else entry + stop
                if hit_tp or hit_sl or t[j] - t_entry >= maxhold:
                    if not (hit_tp or hit_sl):
                        fill = secs["ask_c"][j]
                    pnl = (entry - fill) * 100 * lot - comm * lot
                    net += pnl
                    trades += 1
                    wins += pnl > 0
                    pos = 0
        peak = max(peak, net)
        maxdd = min(maxdd, net - peak)
        j += 1
    return net, trades, wins, maxdd


def split(secs, before):
    t = secs["t"]
    cut = np.searchsorted(t, OOS_SPLIT)
    sl_ = slice(0, cut) if before else slice(cut, len(t))
    return {k: v[sl_] for k, v in secs.items()}


if __name__ == "__main__":
    base = build_seconds()
    fusion = respread(base, 0.031)
    MODELS = [("Std", base, 0.0), ("Fus", fusion, 2.25)]

    print("=== S1 TrendRider — IN-SAMPLE (Jul 20-28) ===")
    print(f"{'model':<5}{'t1':>5}{'t2':>6}{'trail':>7}{'net':>10}{'trades':>8}"
          f"{'win%':>6}{'maxDD':>9}")
    results = []
    for name, secs, comm in MODELS:
        is_ = split(secs, True)
        mv = precompute_move(is_, 900)
        for t1 in (2.0, 2.5, 3.0):
            for t2 in (6.0, 8.0, 10.0):
                for trail in (1.5, 2.5, 3.5):
                    net, tr, w, dd = run_trendrider(is_, mv, t1, t2, trail, comm)
                    results.append((name, t1, t2, trail, net, tr, w, dd))
    for r in sorted(results, key=lambda x: -x[4])[:12]:
        print(f"{r[0]:<5}{r[1]:>5.1f}{r[2]:>6.1f}{r[3]:>7.1f}{r[4]:>+10.2f}"
              f"{r[5]:>8}{100*r[6]/max(r[5],1):>5.0f}%{r[7]:>+9.2f}")

    print("\n=== S2 SpikeFader — IN-SAMPLE (Jul 20-28) ===")
    print(f"{'model':<5}{'F':>5}{'tgt':>6}{'stop':>6}{'hold':>6}{'net':>10}"
          f"{'trades':>8}{'win%':>6}{'maxDD':>9}")
    results2 = []
    for name, secs, comm in MODELS:
        is_ = split(secs, True)
        mv = precompute_move(is_, 60)
        for f in (2.7, 3.5):
            for target in (0.5, 1.0):
                for stop in (2.0, 3.0):
                    for hold in (120, 300):
                        net, tr, w, dd = run_spikefader(is_, mv, f, target, stop, hold, comm)
                        results2.append((name, f, target, stop, hold, net, tr, w, dd))
    for r in sorted(results2, key=lambda x: -x[5])[:12]:
        print(f"{r[0]:<5}{r[1]:>5.1f}{r[2]:>6.1f}{r[3]:>6.1f}{r[4]:>6}"
              f"{r[5]:>+10.2f}{r[6]:>8}{100*r[7]/max(r[6],1):>5.0f}%{r[8]:>+9.2f}")
