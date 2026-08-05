"""v5-restart + ONE new rule: MAX LOCKED PAIRS cap (flatten & re-anchor when
min(longs, shorts) >= cap, realizing the chop loss instead of carrying it).
Matrix: gap {0.45, 0.30} x cap {None, 3, 5, 8} x gate {none, trend, hours}.
Real Fusion feed, 4 months, $1,000 restart banks, v5 conventions
(target $49.5/episode, death at bank+floating <= $10, 30s re-anchor idle)."""
import numpy as np

from trend_gate import er_series, move_series, secs

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0
HOURS = {20, 21, 0, 1, 2, 3, 4, 5}


def run(step, cap=None, gate=None, hours=None):
    t = secs["t"].astype(np.int64)
    n = len(t)
    hour_of = (t // 3600) % 24
    bank = BANK0
    deposits = 1
    deaths = wins = cuts = 0
    low_net = 0.0
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = 0
    while j < n:
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        if anchor_a is None:
            if (t[j] >= idle_until
                    and (gate is None or gate[j])
                    and (hours is None or hour_of[j] in hours)):
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
        flatten = None
        if profit >= TARGET:
            flatten = "win"
        elif cap and min(len(longs), len(shorts)) >= cap:
            flatten = "cut"
        elif bank + profit <= DEATH:
            flatten = "death"
        if flatten:
            bank += profit - COMM_HALF * (len(longs) + len(shorts))
            if flatten == "win":
                wins += 1
            elif flatten == "cut":
                cuts += 1
            if flatten == "death" or bank <= DEATH:
                deaths += 1
                deposits += 1
                bank = BANK0
            anchor_a = None
            idle_until = t[j] + 30
        j += 1
    final_eq = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                       if anchor_a is not None else 0.0)
    return dict(wins=wins, cuts=cuts, deaths=deaths, deposits=deposits,
                eq=final_eq, net=final_eq - deposits * BANK0, low=low_net)


if __name__ == "__main__":
    GATE = er_series(30, 0.25) & move_series(30, 3.0)
    print(f"{'variant':<30}{'wins':>6}{'cuts':>7}{'deaths':>7}{'depos':>7}"
          f"{'NET':>11}{'worst':>11}")
    for step in (0.45, 0.30):
        for gname, g, h in (("no gate", None, None),
                            ("trend gate", GATE, None),
                            ("hours 20-22U00-06", None, HOURS)):
            for cap in (None, 3, 5, 8):
                r = run(step, cap=cap, gate=g, hours=h)
                label = f"{step} {gname} cap={cap or '-'}"
                print(f"{label:<30}{r['wins']:>6}{r['cuts']:>7}{r['deaths']:>7}"
                      f"{r['deposits'] * 1000:>7.0f}{r['net']:>+11.2f}"
                      f"{r['low']:>+11.2f}", flush=True)
    print("\nDONE v5_paircap")
