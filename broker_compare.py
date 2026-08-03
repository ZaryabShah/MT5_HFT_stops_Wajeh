"""Replay v4.2 and v5 under each broker's cost model, plus a prototype of
Wajeh's stop-and-reverse (SAR) idea. Same 10 days of ticks for everything.

Cost models (per 0.01 lot, round trip):
  Exness Standard: spread $0.240, commission $0        -> $0.240
  Fusion ECN:      spread $0.062, commission $0.045    -> $0.107
  Exness Raw:      spread $0.041, commission $0.110    -> $0.151
Spread is remodeled by recentering bid/ask around the tick mid.
"""
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run
from backtest_v5 import run_v5

BROKERS = [
    # name, target half-spread, commission per lot per side
    ("Exness Standard", None, 0.0),          # None = keep original data
    ("Fusion ECN", 0.062 / 2, 2.25),
    ("Exness Raw", 0.041 / 2, 5.50),
]

V42 = dict(DEFAULT)
V42.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=None, regime_mult=4.0))


def respread(secs, half):
    """Rebuild bid/ask around the mid with a new half-spread."""
    out = dict(t=secs["t"])
    for f in ("o", "h", "l", "c"):
        mid = (secs[f"bid_{f}"] + secs[f"ask_{f}"]) / 2
        out[f"bid_{f}"] = mid - half
        out[f"ask_{f}"] = mid + half
    return out


def run_sar(secs, d, comm_side=0.0, lot=0.01):
    """Stop-and-reverse: straddle to start; in-position stop trails at
    distance d and flips direction when hit. Always in the market."""
    t = secs["t"]
    n = len(t)
    pos = 0             # +1 long / -1 short / 0 flat (only at start)
    entry = sl = 0.0
    net = 0.0
    peak = maxdd = 0.0
    flips = 0
    buy_lvl = secs["ask_c"][0] + d
    sell_lvl = secs["bid_c"][0] - d
    for j in range(1, n):
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        if pos == 0:
            if ah >= buy_lvl:
                pos, entry = 1, max(buy_lvl, ao)
                sl = entry - 2 * d
                net -= comm_side * lot
            elif bl <= sell_lvl:
                pos, entry = -1, min(sell_lvl, bo)
                sl = entry + 2 * d
                net -= comm_side * lot
            continue
        if pos == 1:
            sl = max(sl, secs["bid_h"][j] - d)
            if bl <= sl:
                fill = min(sl, bo)
                net += (fill - entry) * 100 * lot - comm_side * lot * 2
                pos, entry = -1, fill
                sl = entry + d
                flips += 1
        else:
            sl = min(sl, secs["ask_l"][j] + d)
            if ah >= sl:
                fill = max(sl, ao)
                net += (entry - fill) * 100 * lot - comm_side * lot * 2
                pos, entry = 1, fill
                sl = entry - d
                flips += 1
        peak = max(peak, net)
        maxdd = min(maxdd, net - peak)
    return net, flips, maxdd


base = build_seconds()

for name, half, comm in BROKERS:
    secs = base if half is None else respread(base, half)
    rng = minute_ranges(secs)
    cfg = dict(V42, commission_per_lot_side=comm * 0.01 / 0.01)  # per lot side
    cfg["commission_per_lot_side"] = comm
    r = run(cfg, secs, rng)
    eps = run_v5(secs, target_usd=49.5, abort_dd=1000)
    v5net = sum(e["pnl"] for e in eps) - comm * 0.01 * sum(e["fills"] for e in eps) * 2
    v5blow = sum(1 for e in eps if e["outcome"] == "BLOWUP")
    v5dd = min(e["min_dd"] for e in eps)
    print(f"\n===== {name} =====")
    print(f"  v4.2: net {r['net']:+9.2f} | maxDD {r['max_dd']:8.2f} | "
          f"{r['n']} cycles | {r['win_rate']*100:.0f}% wins")
    print(f"  v5-A ($1k guard): net {v5net:+9.2f} | worst DD {v5dd:8.2f} | "
          f"{v5blow} blow-ups")

print("\n===== SAR (stop-and-reverse) prototype, per broker =====")
for name, half, comm in BROKERS:
    secs = base if half is None else respread(base, half)
    row = []
    for d in (0.5, 0.9, 1.5, 2.5, 4.0):
        net, flips, maxdd = run_sar(secs, d, comm_side=comm * 0.01)
        row.append(f"d={d}: {net:+8.2f} ({flips} flips, DD {maxdd:.0f})")
    print(f"  {name}:")
    for s in row:
        print(f"    {s}")
