"""v5 budget study: same rules, bigger survival budgets ($500/1000/1500),
plus an effectively-unlimited run to find the worst drawdown the infinite
grid would EVER have hit in these 10 days (= balance for zero blow-ups)."""
from backtest import build_seconds
from backtest_v5 import run_v5

secs = build_seconds()

for label, ladder in [("A: flat 0.01 lots", None), ("B: lot ladder x1.3/3", 1.3)]:
    print(f"\n================ {label}, target +$49.5 ================")
    for abort in [500, 1000, 1500, 100000]:
        eps = run_v5(secs, target_usd=49.5, abort_dd=abort, ladder_mult=ladder)
        wins = [e for e in eps if e["outcome"] == "target"]
        blows = [e for e in eps if e["outcome"] == "BLOWUP"]
        openend = [e for e in eps if e["outcome"] == "OPEN_AT_END"]
        net = sum(e["pnl"] for e in eps)
        worst_dd = min(e["min_dd"] for e in eps)
        tag = "unlimited" if abort == 100000 else f"${abort}"
        extra = ""
        if openend:
            extra = f" | open at end: {openend[0]['pnl']:+.0f}"
        print(f"budget {tag:>9}: {len(wins):>3} wins, {len(blows):>2} blow-ups, "
              f"net {net:+9.2f}, worst DD ever {worst_dd:+9.2f}{extra}")
