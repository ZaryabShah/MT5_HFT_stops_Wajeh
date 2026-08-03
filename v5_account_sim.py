"""v5 with real account mechanics: $1,000 bankroll, account dies when equity
hits ~0, immediately re-deposit $1,000 and restart. 4 months, Fusion costs.
Per spacing: lives, avg lifespan, avg/median peak balance before wash, and
total deposits vs total recovered."""
from datetime import datetime, timezone

import numpy as np

from backtest import build_seconds
from strategies import respread

COMM_HALF = 0.0225      # Fusion commission per 0.01 lot per side
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0            # equity at/below this = stop-out, account dead


def run_account(secs, step):
    t = secs["t"]
    n = len(t)
    bank = BANK0
    lives = []              # dicts: start_t, end_t (death), peak
    life_start = int(t[0])
    peak = BANK0
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = 0
    while j < n:
        if anchor_a is None:
            if t[j] >= idle_until:
                anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
                longs, shorts = [], []
                nb = ns = 1
            j += 1
            continue
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        while ah >= anchor_a + nb * step:
            longs.append(max(anchor_a + nb * step, ao))
            bank -= COMM_HALF
            nb += 1
        while bl <= anchor_b - ns * step:
            shorts.append(min(anchor_b - ns * step, bo))
            bank -= COMM_HALF
            ns += 1
        profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts)
        equity = bank + profit
        peak = max(peak, equity)
        if profit >= TARGET:
            bank += profit - COMM_HALF * (len(longs) + len(shorts))
            anchor_a = None
            idle_until = t[j] + 30
        elif equity <= DEATH:
            lives.append(dict(start=life_start, end=int(t[j]), peak=peak))
            bank = BANK0
            peak = BANK0
            life_start = int(t[j])
            anchor_a = None
            idle_until = t[j] + 30
        j += 1
    # final (surviving) life
    profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts) \
        if anchor_a is not None else 0.0
    return lives, bank + profit, life_start, int(t[-1])


import os

if os.path.exists("data/ticks_fusion.npz"):
    base = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
    print("running on REAL Fusion feed")
else:
    base = respread(build_seconds(), 0.031)
    print("running on modeled feed")
print(f"{'step':>6} {'deaths':>7} {'avg life':>9} {'avg peak':>9} {'med peak':>9} "
      f"{'deposited':>10} {'recovered':>10} {'net':>9}")
for step in (0.20, 0.30, 0.45, 0.60, 0.90, 1.50):
    lives, final_eq, last_start, t_end = run_account(base, step)
    deaths = len(lives)
    spans = [(l["end"] - l["start"]) / 86400 for l in lives]
    peaks = [l["peak"] for l in lives]
    deposited = BANK0 * (deaths + 1)
    recovered = final_eq
    avg_life = np.mean(spans) if spans else (t_end - last_start) / 86400
    avg_peak = np.mean(peaks) if peaks else final_eq
    med_peak = np.median(peaks) if peaks else final_eq
    print(f"{step:>6.2f} {deaths:>7} {avg_life:>8.1f}d {avg_peak:>9.2f} "
          f"{med_peak:>9.2f} {deposited:>10.2f} {recovered:>10.2f} "
          f"{recovered - deposited:>+9.2f}")
print("\navg life = calendar days per $1,000 deposit before wash")
print("avg/med peak = highest balance a $1,000 life reached before dying")
print("net = what 4 months of re-depositing $1,000 actually cost/made")
