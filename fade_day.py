"""THE INVERSE IDEA (user 08-05): v4.8's breakout grid LOSES in day hours
(whipsaw). Mirror it into a FADE grid for those hours: SELL LIMITS above the
anchor, BUY LIMITS below — chop fills both ladders and pays on every
reversion. Exits mirrored: 12%-of-basis target, trail, 8% equity stop,
trend-abort (>=5 one side & <=2 other = fade thesis broken -> flatten),
ladder-consumed flatten, $50 daily breaker. Optional ANTI-trend gate
(trade only when NOT trending). Real Fusion XAUUSD feed, 4 months."""
import numpy as np

from backtest import adaptive_step, minute_ranges
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
ANTI = ~(er_series(30, 0.25) & move_series(30, 3.0))
CONTRACT, LOT, COMM = 100.0, 0.01, 0.0225
CFG = dict(step_mult=0.5, step_floor=0.30, step_cap=2.5)


def wrap(a, b):
    return set(h % 24 for h in range(a, b if b > a else b + 24))


def run_fade(hours, gate=None, sl_pct=0.08, target_pct=0.12, levels=11,
             abort_at=5, abort_other=2, daily_stop=50, regime_mult=6.0):
    t = secs["t"].astype(np.int64)
    n = len(t)
    hour_of = (t // 3600) % 24
    equity = peak_eq = max_dd = 0.0
    cycles = []
    cur_day, day_pnl = -1, 0.0
    idle_until = 0
    i = 0
    while i < n:
        ts = t[i]
        if ts < idle_until or int(hour_of[i]) not in hours or \
                (gate is not None and not gate[i]):
            i += 1
            continue
        spread = secs["ask_c"][i] - secs["bid_c"][i]
        if spread > 0.35:
            i += 1
            continue
        step = adaptive_step(rng, ts, CFG)
        if regime_mult and step < regime_mult * spread:
            i += 1
            continue
        basis = LOT * CONTRACT * step * levels * (levels - 1) / 2 / target_pct
        target = basis * target_pct
        maxloss = basis * sl_pct
        aa, ab = secs["ask_c"][i], secs["bid_c"][i]
        sells = [round(aa + k * step, 3) for k in range(1, levels + 1)]  # limits above
        buys = [round(ab - k * step, 3) for k in range(1, levels + 1)]   # limits below
        longs, shorts = [], []
        realized = peak = 0.0
        outcome = None
        j = i + 1
        while j < n:
            ah, bl = secs["ask_h"][j], secs["bid_l"][j]
            ao, bo = secs["ask_o"][j], secs["bid_o"][j]
            bc, ac = secs["bid_c"][j], secs["ask_c"][j]
            while sells and secs["bid_h"][j] >= sells[0]:
                shorts.append(max(sells.pop(0), bo))
                realized -= COMM
            while buys and secs["ask_l"][j] <= buys[0]:
                longs.append(min(buys.pop(0), ao))
                realized -= COMM
            profit = realized \
                + sum((bc - e) for e in longs) * CONTRACT * LOT \
                + sum((e - ac) for e in shorts) * CONTRACT * LOT
            peak = max(peak, profit)
            if profit >= target:
                outcome = "target"
            elif peak >= target * 0.5 and profit <= peak - target * 0.3:
                outcome = "trail"
            elif profit <= -maxloss:
                outcome = "equitystop"
            elif abort_at and (
                    (len(shorts) >= abort_at and len(longs) <= abort_other) or
                    (len(longs) >= abort_at and len(shorts) <= abort_other)):
                outcome = "trendabort"
            elif (not sells or not buys) and (longs or shorts):
                outcome = "ladder"
            if outcome:
                pnl = profit - COMM * (len(longs) + len(shorts))
                cycles.append(pnl)
                equity += pnl
                peak_eq = max(peak_eq, equity)
                max_dd = min(max_dd, equity - peak_eq)
                idle_until = t[j] + 5
                day = int(t[j]) // 86400
                if day != cur_day:
                    cur_day, day_pnl = day, 0.0
                day_pnl += pnl
                if daily_stop and day_pnl <= -daily_stop:
                    idle_until = (day + 1) * 86400
                i = j
                break
            j += 1
        else:
            break
        i += 1
    wins = sum(1 for p in cycles if p > 0)
    return equity, max_dd, len(cycles), wins


if __name__ == "__main__":
    print(f"{'variant':<34}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}")
    for hlabel, hrs in (("06-20", wrap(6, 20)), ("08-16", wrap(8, 16)),
                        ("06-12", wrap(6, 12)), ("12-18", wrap(12, 18))):
        for glabel, g in (("no gate", None), ("ANTI-trend", ANTI)):
            net, dd, n, w = run_fade(hrs, gate=g)
            print(f"fade {hlabel} {glabel:<12}{net:>+10.2f}{dd:>+10.2f}"
                  f"{n:>6}{100 * w / max(n, 1):>5.0f}%", flush=True)
    for tl, tp in ((7, 0.046), (9, 0.079)):
        net, dd, n, w = run_fade(wrap(8, 16), gate=ANTI, levels=11,
                                 target_pct=tp)
        print(f"fade 08-16 ANTI smalltgt L{tl:<3}{net:>+10.2f}{dd:>+10.2f}"
              f"{n:>6}{100 * w / max(n, 1):>5.0f}%", flush=True)
    print("\nDONE fade_day")
