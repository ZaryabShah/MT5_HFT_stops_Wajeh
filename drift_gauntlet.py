"""DRIFT-B validation gauntlet: hour-neighbor plateau, weekday split,
and exact-cost tick replay (real 01:00 reopen spreads) vs the H1 model."""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
h1 = np.load("data/xau_h1.npy")
ht = h1["time"].astype(np.int64)
ho = h1["open"]
hhour = (ht // 3600) % 24
COST = 0.135
YEARS = list(range(2019, 2027))


def drift(e_h, x_h):
    trades = []
    pos, entry = 0, 0.0
    for i in range(len(ho)):
        h = int(hhour[i])
        if pos == 0 and h == e_h:
            pos, entry = 1, ho[i]
        elif pos == 1 and h == x_h:
            trades.append((int(ht[i]), (ho[i] - entry) - COST))
            pos = 0
    return trades


def summ(trades):
    per = {}
    for ts, p in trades:
        y = datetime.fromtimestamp(int(ts), tz=utc).year
        per[y] = per.get(y, 0.0) + p
    tot = sum(p for _, p in trades)
    posy = sum(1 for y in YEARS if per.get(y, 0) > 0)
    return tot, posy, per


print("=== hour-neighbor plateau (entry->exit, no-swap same-day variants) ===")
for e, x in ((1, 6), (1, 5), (1, 7), (2, 6), (2, 7), (1, 4), (3, 6)):
    tot, posy, _ = summ(drift(e, x))
    print(f"  {e:02d}->0{x}: net {tot:>+8.0f} | positive years {posy}/8",
          flush=True)

print("\n=== weekday split for 01->06 ===")
tr = drift(1, 6)
wd_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
for wd in range(5):
    sub = [p for ts, p in tr
           if datetime.fromtimestamp(int(ts), tz=utc).weekday() == wd]
    w = sum(1 for p in sub if p > 0)
    print(f"  {wd_names[wd]}: net {sum(sub):>+8.0f} ({len(sub):>3}tr "
          f"{100 * w / max(len(sub), 1):.0f}%)", flush=True)

print("\n=== exact-cost tick replay, Apr-Jul 2026 (real reopen spreads) ===")
z = np.load("data/secs_fusion.npz")
t = z["t"].astype(np.int64)
bid_c, ask_c = z["bid_c"], z["ask_c"]
days = np.unique(t // 86400)
net = 0.0
n = 0
worst_spread = 0.0
for d in days:
    e0 = d * 86400 + 1 * 3600
    x0 = d * 86400 + 6 * 3600
    i0 = np.searchsorted(t, e0)
    i1 = np.searchsorted(t, x0) - 1
    if i0 >= len(t) or i1 <= i0 or t[i0] - e0 > 600 or x0 - t[i1] > 600:
        continue
    entry = ask_c[i0]                      # buy at real reopen ask
    exitp = bid_c[i1]                      # sell at real bid before 06:00
    worst_spread = max(worst_spread, ask_c[i0] - bid_c[i0])
    net += (exitp - entry) - 0.045         # commission only; spread is real
    n += 1
h1_2026 = summ(drift(1, 6))[2].get(2026, 0)
print(f"  tick-exact Apr-Jul 2026: net {net:+.2f} over {n} days "
      f"(worst entry spread seen {worst_spread:.3f})")
print(f"  H1-model same period    : {h1_2026:+.0f} (calendar-year 2026 total)")
print("\nDONE drift_gauntlet")
