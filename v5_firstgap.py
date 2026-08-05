"""v5 variations, user request 08-05: (a) WIDER FIRST GAP (dead zone: first
stop at anchor +/- first_gap, then normal step spacing), (b) SMALLER TARGET.
Real Fusion feed, 4 months, $1,000 restart banks, v5 conventions."""
import numpy as np

from trend_gate import secs

COMM_HALF = 0.0225
BANK0 = 1000.0
DEATH = 10.0


def run(step, first_gap=None, target=49.5):
    fg = first_gap if first_gap else step
    t = secs["t"].astype(np.int64)
    n = len(t)
    bank = BANK0
    deposits = 1
    deaths = wins = 0
    low_net = 0.0
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = 0
    while j < n:
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        if anchor_a is None:
            if t[j] >= idle_until:
                anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
                longs, shorts = [], []
                nb = ns = 1
            j += 1
            continue
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        while ah >= anchor_a + fg + (nb - 1) * step:
            longs.append(max(anchor_a + fg + (nb - 1) * step, ao))
            bank -= COMM_HALF
            nb += 1
        while bl <= anchor_b - fg - (ns - 1) * step:
            shorts.append(min(anchor_b - fg - (ns - 1) * step, bo))
            bank -= COMM_HALF
            ns += 1
        profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts)
        low_net = min(low_net, bank + profit - deposits * BANK0)
        if profit >= target:
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
    return dict(wins=wins, deaths=deaths, deposits=deposits,
                net=final_eq - deposits * BANK0, low=low_net)


if __name__ == "__main__":
    print(f"{'variant':<34}{'wins':>6}{'deaths':>7}{'depos':>7}"
          f"{'NET':>11}{'worst':>11}")
    print("--- (a) wider FIRST gap, later gaps unchanged ---")
    for step in (0.45, 0.30):
        for fg in (None, 2, 3, 4):
            g = fg * step if fg else None
            label = f"{step} first={g:.2f}" if g else f"{step} first=step (base)"
            r = run(step, first_gap=g)
            print(f"{label:<34}{r['wins']:>6}{r['deaths']:>7}"
                  f"{r['deposits'] * 1000:>7.0f}{r['net']:>+11.2f}"
                  f"{r['low']:>+11.2f}", flush=True)
    print("--- (b) smaller / bigger TARGET per episode ---")
    for step in (0.45, 0.30):
        for tgt in (10.0, 20.0, 30.0, 49.5, 75.0):
            label = f"{step} target={tgt:.0f}" + (" (base)" if tgt == 49.5 else "")
            r = run(step, target=tgt)
            print(f"{label:<34}{r['wins']:>6}{r['deaths']:>7}"
                  f"{r['deposits'] * 1000:>7.0f}{r['net']:>+11.2f}"
                  f"{r['low']:>+11.2f}", flush=True)
    print("\nDONE v5_firstgap")
