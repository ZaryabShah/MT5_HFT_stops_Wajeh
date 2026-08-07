"""Maker-entry SpikeFader: on a >=T 60s spike, post a LIMIT at the spike
extreme +/- offset (entry at OUR price — no spread paid, offset = extra
edge). TP via limit (maker), SL taker. Active 60s, then cancel.
The adverse-selection question — do we only get filled when it keeps
running? — is answered by the fill simulation itself."""
from datetime import datetime, timezone

import numpy as np

from trend_gate import secs

CONTRACT, LOT, COMM_RT = 100.0, 0.01, 0.045
t = secs["t"].astype(np.int64)
n = len(t)
bid_c, ask_c = secs["bid_c"], secs["ask_c"]
bid_h, bid_l = secs["bid_h"], secs["bid_l"]
ask_h, ask_l = secs["ask_h"], secs["ask_l"]
mid = (bid_c + ask_c) / 2
hour = (t // 3600) % 24
JUN1 = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
US = {15, 16, 17, 18, 19}

lag60 = np.searchsorted(t, t - 60, side="right") - 1
ok60 = (t - t[lag60]) <= 90
mv60 = np.where(ok60, mid - mid[np.clip(lag60, 0, None)], 0.0)


def run(thresh, offset, tp, sl, hours, ttl=60, hold=300):
    trades = []
    fills = signals = 0
    i = 1
    while i < n - 2:
        if int(hour[i]) not in hours or abs(mv60[i]) < thresh:
            i += 1
            continue
        signals += 1
        up = mv60[i] > 0
        limit = (mid[i] + offset) if up else (mid[i] - offset)
        j = i + 1
        fj = None
        while j < n and t[j] - t[i] < ttl:
            if up and bid_h[j] >= limit:          # sell limit filled
                fj = j
                break
            if not up and ask_l[j] <= limit:      # buy limit filled
                fj = j
                break
            j += 1
        if fj is None:
            i = j
            continue
        fills += 1
        entry = limit
        d = -1 if up else 1
        k = fj + 1
        pnl = None
        while k < n and t[k] - t[fj] < hold:
            if d < 0:
                if ask_h[k] >= entry + sl:
                    pnl = -sl * CONTRACT * LOT - COMM_RT
                    break
                if ask_l[k] <= entry - tp:        # buy-limit TP (maker)
                    pnl = tp * CONTRACT * LOT - COMM_RT
                    break
            else:
                if bid_l[k] <= entry - sl:
                    pnl = -sl * CONTRACT * LOT - COMM_RT
                    break
                if bid_h[k] >= entry + tp:
                    pnl = tp * CONTRACT * LOT - COMM_RT
                    break
            k += 1
        if pnl is None:
            k = min(k, n - 1)
            px = ask_c[k] if d < 0 else bid_c[k]
            pnl = ((entry - px) if d < 0 else (px - entry)) * CONTRACT * LOT \
                - COMM_RT
        trades.append((int(t[fj]), pnl))
        i = k + 30
    return trades, signals, fills


if __name__ == "__main__":
    print(f"{'variant':<28}{'':>2}IS / OOS   (fill-rate)")
    for th, off, tp, sl in ((3.5, 0.2, 1.0, 3.0), (3.5, 0.4, 1.0, 3.0),
                            (3.5, 0.6, 1.2, 3.0), (4.5, 0.3, 1.0, 3.0),
                            (4.5, 0.6, 1.5, 3.5)):
        trades, sig, fil = run(th, off, tp, sl, US)
        line = f"SF-LIM t{th} off{off} tp{tp} sl{sl}:"
        for half, f in (("IS", lambda x: x < JUN1), ("OOS", lambda x: x >= JUN1)):
            sub = [p for ts, p in trades if f(ts)]
            if sub:
                w = sum(1 for p in sub if p > 0)
                line += (f"  {half} {sum(sub):>+8.2f} ({len(sub):>4}tr "
                         f"{100 * w / len(sub):>3.0f}%)")
            else:
                line += f"  {half} none"
        line += f"  fills {fil}/{sig}"
        print(line, flush=True)
    print("\nDONE sf_limit")
