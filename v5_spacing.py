"""v5 sensitivity study:
1) spacing sweep x spread model — does tuning the gap help low-spread accounts?
2) same config, started minutes apart — how much does the launch moment matter?
All runs: flat 0.01 lots, +$49.5 target, unlimited budget (true worst DD)."""
from backtest import build_seconds
from backtest_v5 import run_v5
from divergence import respread


def summarize(eps):
    wins = sum(1 for e in eps if e["outcome"] == "target")
    net = sum(e["pnl"] for e in eps)
    worst = min(e["min_dd"] for e in eps)
    return wins, net, worst


base = build_seconds()
narrow = respread(base, 0.031)

print("=== 1) spacing sweep (target +$49.5, unlimited budget, 10 days) ===")
print(f"{'step':>6} | {'Standard $0.24 spread':^34} | {'Narrow $0.062 spread':^34}")
print(f"{'':>6} | {'wins':>5} {'net':>10} {'worstDD':>10}      | {'wins':>5} {'net':>10} {'worstDD':>10}")
for step in (0.45, 0.60, 0.75, 0.90, 1.05, 1.20, 1.50, 2.00):
    wa, na, da = summarize(run_v5(base, step=step, target_usd=49.5, abort_dd=100000))
    wb, nb, db = summarize(run_v5(narrow, step=step, target_usd=49.5, abort_dd=100000))
    print(f"{step:>6.2f} | {wa:>5} {na:>+10.2f} {da:>+10.2f}      | {wb:>5} {nb:>+10.2f} {db:>+10.2f}")

print("\n=== 2) same config (step 0.90, narrow spread), started minutes apart ===")
t0 = int(base["t"][0])
import numpy as np
for offset in (0, 60, 300, 900, 3600):
    idx = int(np.searchsorted(narrow["t"], t0 + offset))
    secs_off = {k: v[idx:] for k, v in narrow.items()}
    w, n, d = summarize(run_v5(secs_off, step=0.90, target_usd=49.5, abort_dd=100000))
    print(f"start +{offset:>5}s: {w:>3} wins, net {n:>+10.2f}, worst DD {d:>+10.2f}")
