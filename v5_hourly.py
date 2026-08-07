"""v5 per-hour-of-day scan + multi-start per-life validation (user request).
Part A: v5-restart (gap 0.45) with anchors allowed ONLY in server hour h,
        for every hour 1-23, full 4 months.
Part B: distribution across 9 starting Mondays: 4-week net (restarts incl.),
        life-1 peak bank (max withdrawable before first death), deaths.
        Configs: no hour gate + the top-2 hours from Part A."""
from datetime import datetime, timedelta, timezone

import numpy as np

from trend_gate import secs

COMM = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0
utc = timezone.utc
T = secs["t"].astype(np.int64)
HOUR = (T // 3600) % 24


def run(step, hours=None, t_from=None, t_to=None):
    lo = np.searchsorted(T, t_from) if t_from else 0
    hi = np.searchsorted(T, t_to) if t_to else len(T)
    bank = BANK0
    deposits = 1
    deaths = wins = 0
    low_net = 0.0
    life1_peak = BANK0
    died_once = False
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = lo
    while j < hi:
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        if anchor_a is None:
            if T[j] >= idle_until and (hours is None or int(HOUR[j]) in hours):
                anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
                longs, shorts = [], []
                nb = ns = 1
            j += 1
            continue
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        while ah >= anchor_a + nb * step:
            longs.append(max(anchor_a + nb * step, ao))
            bank -= COMM
            nb += 1
        while bl <= anchor_b - ns * step:
            shorts.append(min(anchor_b - ns * step, bo))
            bank -= COMM
            ns += 1
        profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts)
        low_net = min(low_net, bank + profit - deposits * BANK0)
        if not died_once:
            life1_peak = max(life1_peak, bank)
        if profit >= TARGET:
            bank += profit - COMM * (len(longs) + len(shorts))
            wins += 1
            anchor_a = None
            idle_until = T[j] + 30
        elif bank + profit <= DEATH:
            deaths += 1
            died_once = True
            deposits += 1
            bank = BANK0
            anchor_a = None
            idle_until = T[j] + 30
        j += 1
    jj = min(j, hi) - 1
    bc, ac = secs["bid_c"][jj], secs["ask_c"][jj]
    fe = bank + (sum(bc - e for e in longs) + sum(e - ac for e in shorts)
                 if anchor_a is not None else 0.0)
    return dict(wins=wins, deaths=deaths, net=fe - deposits * BANK0,
                worst=low_net, life1=life1_peak - BANK0)


if __name__ == "__main__":
    print("=== A: v5 gap 0.45, anchors only in server hour h (full 4mo) ===")
    print(f"{'hour':>5}{'wins':>6}{'deaths':>7}{'NET':>10}{'worst':>10}")
    hour_res = []
    for h in range(1, 24):
        r = run(0.45, hours={h})
        hour_res.append((h, r))
        print(f"{h:>5}{r['wins']:>6}{r['deaths']:>7}{r['net']:>+10.0f}"
              f"{r['worst']:>+10.0f}", flush=True)
    best = sorted(hour_res, key=lambda x: -x[1]["net"])[:2]
    b1, b2 = best[0][0], best[1][0]
    print(f"\ntop hours: {b1}, {b2}")

    print("\n=== B: 9 starting Mondays x 4 weeks — distribution ===")
    d0 = datetime(2026, 4, 6, tzinfo=utc)
    starts = [d0 + timedelta(weeks=2 * k) for k in range(9)]
    for label, hrs in (("no gate", None), (f"hour {b1}", {b1}),
                       (f"hour {b2}", {b2})):
        nets, lifes, deaths = [], [], []
        for s in starts:
            a = int(s.timestamp())
            r = run(0.45, hours=hrs, t_from=a,
                    t_to=a + 28 * 86400)
            nets.append(r["net"])
            lifes.append(r["life1"])
            deaths.append(r["deaths"])
        nets_s = sorted(nets)
        print(f"{label:<10} 4wk nets: " + " ".join(f"{x:+.0f}" for x in nets)
              + f"\n{'':<10} median {nets_s[4]:+.0f} | positive "
              f"{sum(1 for x in nets if x > 0)}/9 | total deaths "
              f"{sum(deaths)} | median life-1 peak {sorted(lifes)[4]:+.0f}",
              flush=True)
    print("\nDONE v5_hourly")
