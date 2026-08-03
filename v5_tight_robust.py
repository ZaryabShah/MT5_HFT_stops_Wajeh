"""Robustness check: the star cell (0.20 spacing on cheap spread) run from
5 different start moments, with Fusion's real commission included."""
import numpy as np

from backtest import build_seconds
from backtest_v5 import run_v5
from v5_tight import respread

COMM_RT = 0.045          # Fusion: $4.50/lot RT -> per 0.01 lot round trip

base = build_seconds()
narrow = respread(base, 0.031)
t0 = int(narrow["t"][0])

print("step 0.20, narrow spread + Fusion commission, unlimited budget:")
for offset in (0, 60, 300, 900, 3600):
    idx = int(np.searchsorted(narrow["t"], t0 + offset))
    secs = {k: v[idx:] for k, v in narrow.items()}
    eps = run_v5(secs, step=0.20, target_usd=49.5, abort_dd=100000)
    wins = sum(1 for e in eps if e["outcome"] == "target")
    fills = sum(e["fills"] for e in eps)
    net = sum(e["pnl"] for e in eps) - fills * COMM_RT
    worst = min(e["min_dd"] for e in eps)
    print(f"  start +{offset:>5}s: {wins:>3} wins, {fills:>6,} fills, "
          f"net {net:>+10.2f} (incl comm), maxDD {worst:>+9.2f}")

print("\nsame test for step 0.30:")
for offset in (0, 60, 300, 900, 3600):
    idx = int(np.searchsorted(narrow["t"], t0 + offset))
    secs = {k: v[idx:] for k, v in narrow.items()}
    eps = run_v5(secs, step=0.30, target_usd=49.5, abort_dd=100000)
    wins = sum(1 for e in eps if e["outcome"] == "target")
    fills = sum(e["fills"] for e in eps)
    net = sum(e["pnl"] for e in eps) - fills * COMM_RT
    worst = min(e["min_dd"] for e in eps)
    print(f"  start +{offset:>5}s: {wins:>3} wins, {fills:>6,} fills, "
          f"net {net:>+10.2f} (incl comm), maxDD {worst:>+9.2f}")
