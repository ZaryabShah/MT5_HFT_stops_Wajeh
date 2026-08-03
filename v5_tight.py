"""v5 ultra-tight spacing sweep: 0.20-0.40, both spread models, unlimited
budget, with worst drawdown for each."""
from backtest import build_seconds
from backtest_v5 import run_v5


def respread(secs, half):
    out = dict(t=secs["t"])
    for f in ("o", "h", "l", "c"):
        mid = (secs[f"bid_{f}"] + secs[f"ask_{f}"]) / 2
        out[f"bid_{f}"] = mid - half
        out[f"ask_{f}"] = mid + half
    return out


def summarize(eps):
    wins = sum(1 for e in eps if e["outcome"] == "target")
    net = sum(e["pnl"] for e in eps)
    worst = min(e["min_dd"] for e in eps)
    return wins, net, worst


base = build_seconds()
narrow = respread(base, 0.031)

print("=== v5 tight spacing (target +$49.5, unlimited budget, 10 days) ===")
print(f"{'step':>6} | {'Standard $0.24 spread':^36} | {'Narrow $0.062 spread':^36}")
print(f"{'':>6} | {'wins':>5} {'net':>10} {'maxDD':>11}       | {'wins':>5} {'net':>10} {'maxDD':>11}")
for step in (0.20, 0.25, 0.30, 0.35, 0.40):
    wa, na, da = summarize(run_v5(base, step=step, target_usd=49.5, abort_dd=100000))
    wb, nb, db = summarize(run_v5(narrow, step=step, target_usd=49.5, abort_dd=100000))
    print(f"{step:>6.2f} | {wa:>5} {na:>+10.2f} {da:>+11.2f}       | {wb:>5} {nb:>+10.2f} {db:>+11.2f}")
