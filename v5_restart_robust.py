"""Start-offset stress test for the v5-restart 'jackpot' cells (0.30, 0.45)
on the REAL Fusion feed. Self-contained copy of the account simulator."""
import numpy as np

from backtest import build_seconds

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0


def run_account(secs, step):
    t = secs["t"]
    n = len(t)
    bank = BANK0
    deaths = 0
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
        if profit >= TARGET:
            bank += profit - COMM_HALF * (len(longs) + len(shorts))
            anchor_a = None
            idle_until = t[j] + 30
        elif bank + profit <= DEATH:
            deaths += 1
            bank = BANK0
            anchor_a = None
            idle_until = t[j] + 30
        j += 1
    final = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                    if anchor_a is not None else 0.0)
    deposited = BANK0 * (deaths + 1)
    return deaths, deposited, final, final - deposited + BANK0 * deaths  # net = recovered - deposited


secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
t0 = int(secs["t"][0])
for step in (0.30, 0.45):
    print(f"\n=== v5-restart step {step}, real feed, 5 start times ===")
    for off in (0, 900, 3600, 14400, 86400):
        idx = int(np.searchsorted(secs["t"], t0 + off))
        sub = {k: v[idx:] for k, v in secs.items()}
        deaths, deposited, final, _ = run_account(sub, step)
        print(f"start +{off:>6}s: {deaths:>2} deaths | deposited {deposited:>8.2f} | "
              f"recovered {final:>9.2f} | net {final - deposited:>+10.2f}")
