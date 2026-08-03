"""v5-restart with a WITHDRAWAL rule: any balance above CAP is swept out
(banked safely) whenever a round closes. Death then costs at most CAP.
Compares no-sweep vs sweep-to-2500 vs sweep-to-5000, step 0.45, real feed."""
from datetime import datetime, timezone

from backtest import build_seconds

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0


def run(secs, step, cap=None):
    t = secs["t"]
    n = len(t)
    bank = BANK0
    withdrawn = 0.0
    deposits = 1
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
            if cap and bank > cap:
                withdrawn += bank - cap
                bank = cap
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
    net = withdrawn + final_eq - deposits * BANK0
    return deaths, deposits, withdrawn, final_eq, net


secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
print(f"{'variant':<16}{'deaths':>7}{'deposited':>10}{'withdrawn':>11}"
      f"{'in account':>11}{'NET':>11}")
for label, cap in [("no sweep", None), ("sweep to 2500", 2500),
                   ("sweep to 5000", 5000)]:
    deaths, deps, wd, eq, net = run(secs, 0.45, cap)
    print(f"{label:<16}{deaths:>7}{deps * 1000:>10.2f}{wd:>11.2f}"
          f"{eq:>11.2f}{net:>+11.2f}")
