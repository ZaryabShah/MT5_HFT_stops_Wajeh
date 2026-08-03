"""Show exactly where the two spread models' v5 paths split apart."""
from datetime import datetime, timezone

from backtest import build_seconds
from backtest_v5 import run_v5


def respread(secs, half):
    out = dict(t=secs["t"])
    for f in ("o", "h", "l", "c"):
        mid = (secs[f"bid_{f}"] + secs[f"ask_{f}"]) / 2
        out[f"bid_{f}"] = mid - half
        out[f"ask_{f}"] = mid + half
    return out


def fmt(eps, i):
    if i >= len(eps):
        return "—"
    e = eps[i]
    t = datetime.fromtimestamp(e["t"], tz=timezone.utc).strftime("%m-%d %H:%M")
    return f'{t} {e["outcome"][:6]:<6} {e["pnl"]:+8.1f} ({e["hours"]:5.1f}h {e["fills"]:3d}f)'


base = build_seconds()
a = run_v5(base, target_usd=49.5, abort_dd=100000)
b = run_v5(respread(base, 0.031), target_usd=49.5, abort_dd=100000)
print(f'{"#":>3} {"Standard spread ($0.24)":<42} {"Narrow spread ($0.062)":<42}')
for i in range(14):
    print(f"{i+1:>3} {fmt(a, i):<42} {fmt(b, i):<42}")
print(f"... totals: {len(a)} episodes vs {len(b)} episodes")
print(f"nets: {sum(e['pnl'] for e in a):+.2f} vs {sum(e['pnl'] for e in b):+.2f}")
print(f"worst DD: {min(e['min_dd'] for e in a):+.2f} vs {min(e['min_dd'] for e in b):+.2f}")
