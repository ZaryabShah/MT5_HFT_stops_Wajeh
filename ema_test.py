"""EMA-cross strategies on the real XAUUSD Fusion feed (user request).
M1 mid closes; enter on fast/slow EMA cross, exit on opposite cross or SL.
Costs: real avg half-spread at entry+exit + Fusion commission. 0.01 lots."""
import numpy as np

from trend_gate import secs

CONTRACT, LOT, COMM_RT = 100.0, 0.01, 0.045

t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2
spr = secs["ask_c"] - secs["bid_c"]
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
last = np.append(idx[1:], len(t)) - 1
m_close = mid[last]
m_low = np.array([secs["bid_l"][idx[i]:last[i] + 1].min() for i in range(len(uniq))])
m_high = np.array([secs["ask_h"][idx[i]:last[i] + 1].max() for i in range(len(uniq))])
m_spr = spr[last]
m_hour = (uniq * 60 // 3600) % 24


def ema(x, n):
    a = 2 / (n + 1)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def run(fast, slow, sl=None, hours=None):
    ef, es = ema(m_close, fast), ema(m_close, slow)
    pos = 0          # +1 long, -1 short
    entry = 0.0
    net = dd = peak = 0.0
    trades = wins = 0
    for i in range(slow + 1, len(m_close)):
        cross_up = ef[i] > es[i] and ef[i - 1] <= es[i - 1]
        cross_dn = ef[i] < es[i] and ef[i - 1] >= es[i - 1]
        half = m_spr[i] / 2
        if pos > 0:
            stop_hit = sl and (entry - m_low[i]) >= sl
            if stop_hit or cross_dn:
                px = (entry - sl) if stop_hit else m_close[i] - half
                pnl = (px - entry) * CONTRACT * LOT - COMM_RT
                net += pnl
                trades += 1
                wins += pnl > 0
                peak = max(peak, net)
                dd = min(dd, net - peak)
                pos = 0
        elif pos < 0:
            stop_hit = sl and (m_high[i] - entry) >= sl
            if stop_hit or cross_up:
                px = (entry + sl) if stop_hit else m_close[i] + half
                pnl = (entry - px) * CONTRACT * LOT - COMM_RT
                net += pnl
                trades += 1
                wins += pnl > 0
                peak = max(peak, net)
                dd = min(dd, net - peak)
                pos = 0
        if pos == 0 and (hours is None or m_hour[i] in hours):
            if cross_up:
                pos, entry = 1, m_close[i] + half
            elif cross_dn:
                pos, entry = -1, m_close[i] - half
    return net, dd, trades, wins


if __name__ == "__main__":
    NIGHT = {20, 21, 0, 1, 2, 3, 4, 5}
    print(f"{'variant':<28}{'net':>10}{'maxDD':>10}{'trades':>8}{'win%':>6}")
    for f, s in ((5, 20), (9, 15), (9, 21), (12, 26), (20, 50)):
        for sl in (None, 2.0, 4.0):
            for hl, hrs in (("all", None), ("night", NIGHT)):
                net, dd, n, w = run(f, s, sl=sl, hours=hrs)
                print(f"EMA{f}/{s} sl={sl or '-':<4} {hl:<6}"
                      f"{net:>+10.2f}{dd:>+10.2f}{n:>8}"
                      f"{100 * w / max(n, 1):>5.0f}%", flush=True)
    print("\nDONE ema_test")
