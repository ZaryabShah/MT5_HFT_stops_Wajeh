"""Test the user's anchor-determinism idea: recenter every grid on the
nearest Q-dollar multiple (so live and sim compute the SAME ladder whenever
their anchor mids round the same way). Does quantizing cost edge? Full
4-month v4.8 stack, Q in {None, 0.5, 1.0, 2.0}, plus halves for each."""
from datetime import datetime, timezone

from backtest import run
from trend_gate import V46, er_series, move_series, rng, secs

GATE = er_series(30, 0.25) & move_series(30, 3.0)
MID = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
BASE = dict(V46, hours={20, 21, 0, 1, 2, 3, 4, 5}, gate_series=GATE)

print(f"{'variant':<16}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}"
      f"  | Apr-May | Jun-Jul")
for q in (None, 0.5, 1.0, 2.0):
    cfg = dict(BASE, anchor_quant=q)
    r = run(cfg, secs, rng)
    a = run(cfg, secs, rng, t_to=MID)
    b = run(cfg, secs, rng, t_from=MID)
    print(f"Q={str(q):<14}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate']*100:>5.0f}%  | {a['net']:>+8.2f} | {b['net']:>+8.2f}",
          flush=True)
print("\nDONE anchor_quant_test")
