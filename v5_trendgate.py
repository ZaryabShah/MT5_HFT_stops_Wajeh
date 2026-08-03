"""v5-restart with the v4.7 trend gate on anchor placement (ER(30m)>=0.25
AND |move30m|>=$3). Real feed, 4 months, $1,000 restarts, steps 0.45/0.30."""
import numpy as np

from backtest import build_seconds
from trend_gate import er_series, move_series

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0


def run(secs, step, gate=None):
    t = secs["t"]
    n = len(t)
    bank = BANK0
    deposits = 1
    deaths = 0
    wins = 0
    low_net = 0.0          # worst (equity - deposits) seen
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = 0
    while j < n:
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        if anchor_a is None:
            if t[j] >= idle_until and (gate is None or gate[j]):
                anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
                longs, shorts = [], []
                nb = ns = 1
            j += 1
            continue
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        while ah >= anchor_a + nb * step:
            longs.append(max(anchor_a + nb * step, ao))
            bank -= COMM_HALF
            nb += 1
        while bl <= anchor_b - ns * step:
            shorts.append(min(anchor_b - ns * step, bo))
            bank -= COMM_HALF
            ns += 1
        profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts)
        low_net = min(low_net, bank + profit - deposits * BANK0)
        if profit >= TARGET:
            bank += profit - COMM_HALF * (len(longs) + len(shorts))
            wins += 1
            anchor_a = None
            idle_until = t[j] + 30
        elif bank + profit <= DEATH:
            deaths += 1
            deposits += 1
            bank = BANK0
            anchor_a = None
            idle_until = t[j] + 30
        j += 1
    final_eq = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                       if anchor_a is not None else 0.0)
    return wins, deaths, deposits, final_eq, final_eq - deposits * BANK0, low_net


secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
gate = (er_series(30, 0.25) & move_series(30, 3.0))
print(f"{'variant':<26}{'wins':>6}{'deaths':>7}{'deposited':>10}{'final eq':>10}"
      f"{'NET':>11}{'worst net':>11}")
for step in (0.45, 0.30):
    for label, g in [("no gate (baseline)", None), ("v4.7 trend gate", gate)]:
        w, d, dep, eq, net, low = run(secs, step, g)
        print(f"gap {step} {label:<19}{w:>6}{d:>7}{dep * 1000:>10.0f}"
              f"{eq:>10.2f}{net:>+11.2f}{low:>+11.2f}")
