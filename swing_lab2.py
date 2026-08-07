"""SWING LAB v2 — swap-aware. Today's Fusion rates as forward estimate:
long -$0.5804 / short +$0.2769 per 0.01 per night, Wednesday x3.
(Historical swaps were smaller in the 0%-rate years — noted, unknowable.)
New: the drift SPLIT — 20->23 (pre-rollover leg) vs 01->06 (post-rollover,
ZERO-swap) — if the drift lives post-midnight, it's a swap-free anomaly."""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
d1 = np.load("data/xau_d1.npy")
h1 = np.load("data/xau_h1.npy")
COST = 0.135
SWL, SWS = -0.5804, 0.2769

dt = d1["time"].astype(np.int64)
dh, dl, dc, do = d1["high"], d1["low"], d1["close"], d1["open"]
ht = h1["time"].astype(np.int64)
ho, hc = h1["open"], h1["close"]
hh, hl = h1["high"], h1["low"]
hhour = (ht // 3600) % 24
YEARS = list(range(2011, 2027))


def swap_nights(te, tx, direction):
    """Sum swap for midnights crossed (Wed x3). Server epochs."""
    d0 = te // 86400
    d1_ = tx // 86400
    total = 0.0
    rate = SWL if direction > 0 else SWS
    for d in range(int(d0) + 1, int(d1_) + 1):
        wd = (d + 4) % 7          # 0=Sun..? epoch day 0 = Thu -> (d+4)%7: 0=Mon
        mult = 3 if wd == 2 else 1  # Wednesday
        total += rate * mult
    return total


def show(name, trades):
    per = {}
    for ts, p in trades:
        y = datetime.fromtimestamp(int(ts), tz=utc).year
        per[y] = per.get(y, 0.0) + p
    tot = sum(p for _, p in trades)
    eq = np.cumsum([p for _, p in trades]) if trades else np.array([0.0])
    dd = float(np.min(eq - np.maximum.accumulate(eq))) if len(eq) else 0.0
    w = sum(1 for _, p in trades if p > 0)
    pos_years = sum(1 for y in YEARS if per.get(y, 0) > 0)
    ny = sum(1 for y in YEARS if y in per)
    print(f"{name:<24}{tot:>+9.0f}{dd:>+8.0f}{len(trades):>6}"
          f"{(100 * w / len(trades) if trades else 0):>5.0f}%"
          f"{pos_years:>4}/{ny:<3} "
          + " ".join(f"{per.get(y, 0):+.0f}" for y in YEARS if y in per),
          flush=True)


print(f"{'family (swap-adjusted)':<24}{'net':>9}{'maxDD':>8}{'tr':>6}"
      f"{'win%':>6}{'yr+':>7}")

# --- ODRIFT full 20->06 (crosses midnight: pays swap) ---
trades = []
pos, entry, te = 0, 0.0, 0
for i in range(len(hc)):
    h = int(hhour[i])
    if pos == 0 and h == 20:
        pos, entry, te = 1, ho[i], int(ht[i])
    elif pos == 1 and h == 6:
        pnl = (ho[i] - entry) - COST + swap_nights(te, int(ht[i]), 1)
        trades.append((int(ht[i]), pnl))
        pos = 0
show("ODRIFT 20->06 (swap)", trades)

# --- drift split: pre-rollover leg 20->23 close (no midnight) ---
trades = []
pos, entry = 0, 0.0
for i in range(len(hc)):
    h = int(hhour[i])
    if pos == 0 and h == 20:
        pos, entry = 1, ho[i]
    elif pos == 1 and h == 23:
        trades.append((int(ht[i]), (hc[i] - entry) - COST))
        pos = 0
show("DRIFT-A 20->24 no-swap", trades)

# --- post-rollover leg 01->06 (no midnight crossed: ZERO swap) ---
trades = []
pos, entry = 0, 0.0
for i in range(len(hc)):
    h = int(hhour[i])
    if pos == 0 and h == 1:
        pos, entry = 1, ho[i]
    elif pos == 1 and h == 6:
        trades.append((int(ht[i]), (ho[i] - entry) - COST))
        pos = 0
show("DRIFT-B 01->06 no-swap", trades)

# --- MAREG D1 long/flat with swap ---
def sma(x, n):
    s = np.full(len(x), np.nan)
    c = np.cumsum(np.insert(x, 0, 0.0))
    s[n - 1:] = (c[n:] - c[:-n]) / n
    return s

s50 = sma(dc, 50)
trades = []
pos, entry, te = 0, 0.0, 0
for i in range(51, len(dc)):
    want = 1 if (dc[i] > s50[i] and s50[i] > s50[i - 5]) else 0
    if pos != want:
        if pos == 1:
            pnl = (dc[i] - entry) - COST + swap_nights(te, int(dt[i]), 1)
            trades.append((int(dt[i]), pnl))
        pos, entry, te = want, dc[i], int(dt[i])
show("MAREG D1 L/flat (swap)", trades)

# --- DONC D1 55/20 with swap ---
trades = []
pos, entry, te = 0, 0.0, 0
for i in range(56, len(dc)):
    if pos == 0:
        if dc[i] > dh[i - 55:i].max():
            pos, entry, te = 1, dc[i], int(dt[i])
        elif dc[i] < dl[i - 55:i].min():
            pos, entry, te = -1, dc[i], int(dt[i])
    elif pos > 0 and dc[i] < dl[i - 20:i].min():
        trades.append((int(dt[i]), (dc[i] - entry) - COST
                       + swap_nights(te, int(dt[i]), 1)))
        pos = 0
    elif pos < 0 and dc[i] > dh[i - 20:i].max():
        trades.append((int(dt[i]), (entry - dc[i]) - COST
                       + swap_nights(te, int(dt[i]), -1)))
        pos = 0
show("DONC D1 55/20 (swap)", trades)

# --- WMOM weekly with swap ---
wk = {}
for i in range(len(dc)):
    d = datetime.fromtimestamp(int(dt[i]), tz=utc)
    key = (d.isocalendar().year, d.isocalendar().week)
    wk.setdefault(key, []).append(i)
keys = sorted(wk)
trades = []
for k in range(1, len(keys)):
    prev, cur = wk[keys[k - 1]], wk[keys[k]]
    ret = dc[prev[-1]] - dc[prev[0] - 1] if prev[0] > 0 else 0
    d0, dz = cur[0], cur[-1]
    sgn = 1 if ret > 0 else -1
    pnl = (dc[dz] - do[d0]) * sgn - COST \
        + swap_nights(int(dt[d0]), int(dt[dz]), sgn)
    trades.append((int(dt[dz]), pnl))
show("WMOM weekly (swap)", trades)
print("\nDONE swing_lab2")
