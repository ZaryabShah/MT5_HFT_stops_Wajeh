"""SWING LAB — gold at bar scale, 16 years (2010-2026), where costs are
negligible ($0.135/0.01-lot RT vs $20-40 targets). Families judged PER YEAR
and against buy-and-hold. All P/L per 0.01 lot (= $ per oz).
  BH    buy & hold (the benchmark every family must beat risk-adjusted)
  DONC  Donchian channel breakout (turtle-style), D1 and H1, long+short
  MAREG MA-regime: long above rising SMA50(D1); variant w/ shorts below
  PULL  pullback-buy in uptrend (dip to SMA20-0.5*ATR while above SMA50)
  WMOM  weekly momentum (hold next week in last week's direction)
  ODRIFT overnight-session drift: long server 20:00->06:00 only (our
         session asymmetry, tested at position scale across 16 years)
"""
from datetime import datetime, timezone

import numpy as np

utc = timezone.utc
d1 = np.load("data/xau_d1.npy")
h1 = np.load("data/xau_h1.npy")
COST = 0.135          # $ per 0.01-lot round trip (spread+commission)

dt = d1["time"].astype(np.int64)
do, dh, dl, dc = d1["open"], d1["high"], d1["low"], d1["close"]
dyear = np.array([datetime.fromtimestamp(int(x), tz=utc).year for x in dt])

ht = h1["time"].astype(np.int64)
ho, hc = h1["open"], h1["close"]
hhour = (ht // 3600) % 24
hyear = np.array([datetime.fromtimestamp(int(x), tz=utc).year for x in ht])

YEARS = list(range(2011, 2027))


def yearly(trades):
    """trades: list of (close_epoch, pnl). Returns {year: net} + stats."""
    per = {}
    for ts, p in trades:
        y = datetime.fromtimestamp(int(ts), tz=utc).year
        per[y] = per.get(y, 0.0) + p
    eq = np.cumsum([p for _, p in trades]) if trades else np.array([0.0])
    dd = float(np.min(eq - np.maximum.accumulate(eq))) if len(eq) else 0.0
    w = sum(1 for _, p in trades if p > 0)
    return per, sum(p for _, p in trades), dd, len(trades), w


def show(name, trades):
    per, tot, dd, n, w = yearly(trades)
    pos_years = sum(1 for y in YEARS if per.get(y, 0) > 0)
    line = f"{name:<22}{tot:>+9.0f}{dd:>+8.0f}{n:>6}"
    line += f"{(100 * w / n if n else 0):>5.0f}%{pos_years:>4}/16  "
    line += " ".join(f"{per.get(y, 0):+.0f}" for y in YEARS)
    print(line, flush=True)


print(f"{'family':<22}{'net':>9}{'maxDD':>8}{'tr':>6}{'win%':>6}{'yr+':>7}  "
      + " ".join(str(y)[2:] for y in YEARS))

# BH
show("BH buy&hold", [(int(dt[i]), dc[i] - dc[i - 1]) for i in range(1, len(dc))])

# DONC D1: enter on N-day extreme, exit on M-day opposite extreme
for N, M in ((20, 10), (55, 20)):
    trades = []
    pos, entry = 0, 0.0
    for i in range(N + 1, len(dc)):
        hiN = dh[i - N:i].max()
        loN = dl[i - N:i].min()
        hiM = dh[i - M:i].max()
        loM = dl[i - M:i].min()
        if pos == 0:
            if dc[i] > hiN:
                pos, entry = 1, dc[i]
            elif dc[i] < loN:
                pos, entry = -1, dc[i]
        elif pos > 0 and dc[i] < loM:
            trades.append((int(dt[i]), (dc[i] - entry) - COST))
            pos = 0
        elif pos < 0 and dc[i] > hiM:
            trades.append((int(dt[i]), (entry - dc[i]) - COST))
            pos = 0
    show(f"DONC D1 {N}/{M} L+S", trades)

# DONC H1 120/60
for N, M in ((120, 60), (240, 120)):
    trades = []
    pos, entry = 0, 0.0
    hh, hl = h1["high"], h1["low"]
    for i in range(N + 1, len(hc)):
        if pos == 0:
            if hc[i] > hh[i - N:i].max():
                pos, entry = 1, hc[i]
            elif hc[i] < hl[i - N:i].min():
                pos, entry = -1, hc[i]
        elif pos > 0 and hc[i] < hl[i - M:i].min():
            trades.append((int(ht[i]), (hc[i] - entry) - COST))
            pos = 0
        elif pos < 0 and hc[i] > hh[i - M:i].max():
            trades.append((int(ht[i]), (entry - hc[i]) - COST))
            pos = 0
    show(f"DONC H1 {N}/{M} L+S", trades)

# MAREG D1
sma50 = np.convolve(dc, np.ones(50) / 50, mode="valid")   # aligned: sma50[i] = mean(dc[i:i+50])
def sma(x, n):
    s = np.full(len(x), np.nan)
    c = np.cumsum(np.insert(x, 0, 0.0))
    s[n - 1:] = (c[n:] - c[:-n]) / n
    return s

s50 = sma(dc, 50)
s20 = sma(dc, 20)
tr = np.maximum(dh - dl, np.maximum(abs(dh - np.roll(dc, 1)),
                                    abs(dl - np.roll(dc, 1))))
atr = sma(tr, 14)
for use_short, lab in ((False, "long/flat"), (True, "long/short")):
    trades = []
    pos, entry = 0, 0.0
    for i in range(51, len(dc)):
        want = 0
        if dc[i] > s50[i] and s50[i] > s50[i - 5]:
            want = 1
        elif use_short and dc[i] < s50[i] and s50[i] < s50[i - 5]:
            want = -1
        if pos != want:
            if pos != 0:
                pnl = (dc[i] - entry) if pos > 0 else (entry - dc[i])
                trades.append((int(dt[i]), pnl - COST))
            pos, entry = want, dc[i]
    show(f"MAREG D1 {lab}", trades)

# PULL D1
trades = []
pos, entry, stop = 0, 0.0, 0.0
for i in range(51, len(dc)):
    if pos == 0:
        if dc[i] > s50[i] and dc[i] <= s20[i] - 0.5 * atr[i]:
            pos, entry = 1, dc[i]
            stop = entry - 2 * atr[i]
    else:
        if dl[i] <= stop:
            trades.append((int(dt[i]), (stop - entry) - COST))
            pos = 0
        elif dc[i] >= s20[i]:
            trades.append((int(dt[i]), (dc[i] - entry) - COST))
            pos = 0
show("PULL D1 dip-buy", trades)

# WMOM weekly momentum
wk = {}
for i in range(len(dc)):
    d = datetime.fromtimestamp(int(dt[i]), tz=utc)
    key = (d.isocalendar().year, d.isocalendar().week)
    wk.setdefault(key, []).append(i)
keys = sorted(wk)
trades = []
for k in range(1, len(keys)):
    prev = wk[keys[k - 1]]
    cur = wk[keys[k]]
    ret = dc[prev[-1]] - dc[prev[0] - 1] if prev[0] > 0 else 0
    d0, d1_ = cur[0], cur[-1]
    pnl = (dc[d1_] - do[d0]) * (1 if ret > 0 else -1)
    trades.append((int(dt[d1_]), pnl - COST))
show("WMOM weekly", trades)

# ODRIFT: long server 20:00 -> 06:00 (H1 bars), flat rest
trades = []
pos, entry = 0, 0.0
for i in range(len(hc)):
    h = int(hhour[i])
    if pos == 0 and h == 20:
        pos, entry = 1, ho[i]
    elif pos == 1 and h == 6:
        trades.append((int(ht[i]), (ho[i] - entry) - COST))
        pos = 0
show("ODRIFT 20->06 long", trades)
# inverse control: day-session hold
trades = []
pos, entry = 0, 0.0
for i in range(len(hc)):
    h = int(hhour[i])
    if pos == 0 and h == 6:
        pos, entry = 1, ho[i]
    elif pos == 1 and h == 20:
        trades.append((int(ht[i]), (ho[i] - entry) - COST))
        pos = 0
show("control: 06->20 long", trades)
print("\nDONE swing_lab")
