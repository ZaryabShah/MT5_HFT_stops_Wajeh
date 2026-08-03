"""v5-restart with session windows, real feed, 4 months, $1,000 restarts.
Variant A: window gates NEW anchors only (open rounds run to completion).
Variant B: window also FORCE-CLOSES all positions when it shuts."""
from datetime import datetime, timezone

from backtest import build_seconds

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0


def run(secs, step, hours=None, force_close=False):
    t = secs["t"]
    n = len(t)
    bank = BANK0
    deposits = 1
    deaths = 0
    wins = 0
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = 0
    while j < n:
        hr = int(t[j] // 3600) % 24
        in_win = hours is None or hr in hours
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        if anchor_a is None:
            if in_win and t[j] >= idle_until:
                anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
                longs, shorts = [], []
                nb = ns = 1
            j += 1
            continue
        if force_close and not in_win and (longs or shorts):
            bank += sum(bc - e for e in longs) + sum(e - ac for e in shorts) \
                - COMM_HALF * (len(longs) + len(shorts))
            longs, shorts = [], []
            anchor_a = None
            if bank <= DEATH:
                deaths += 1
                deposits += 1
                bank = BANK0
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
    return wins, deaths, deposits, final_eq, final_eq - deposits * BANK0


secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
CASES = [
    ("24h baseline", None, False),
    ("22-06 anchors only", {22, 23, 0, 1, 2, 3, 4, 5}, False),
    ("00-06 anchors only", {0, 1, 2, 3, 4, 5}, False),
    ("London 07-15 anchors", set(range(7, 15)), False),
    ("US 12-20 anchors", set(range(12, 20)), False),
    ("22-06 + force-close", {22, 23, 0, 1, 2, 3, 4, 5}, True),
]
for step in (0.45, 0.30):
    print(f"\n===== gap {step}, 4 months, real feed =====")
    print(f"{'variant':<22}{'wins':>6}{'deaths':>7}{'deposited':>10}"
          f"{'final eq':>10}{'NET':>11}")
    for label, hrs, fc in CASES:
        w, d, dep, eq, net = run(secs, step, hrs, fc)
        print(f"{label:<22}{w:>6}{d:>7}{dep * 1000:>10.0f}{eq:>10.2f}{net:>+11.2f}")
