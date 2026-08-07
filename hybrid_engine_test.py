"""USER'S PROPOSAL, MEASURED: live bot = tick-level broker fills (resting
stops fill on the broker's quote stream no matter what the bot does) +
1-second exit checks (bot-side decisions). The hybrid engine models exactly
that: tick bars for fills, exit logic gated to each second's last tick.
Compare against pure-1s (+4374.06) and pure-tick (+2906.17), 4 months +
halves + Aug 7 morning."""
from datetime import datetime, timezone

from backtest import DEFAULT, minute_ranges, run
from tick_exact_test import BASE, make_gate, tick_bars

utc = timezone.utc
MID = int(datetime(2026, 6, 1, tzinfo=utc).timestamp())

secs = tick_bars("data/ticks_fusion.npz")
rng = minute_ranges(secs)
cfg = dict(BASE, hours={20, 21, 0, 1, 2, 3, 4, 5},
           gate_series=make_gate(secs), exit_on_sec_end=True)
r = run(cfg, secs, rng)
a = run(cfg, secs, rng, t_to=MID)
b = run(cfg, secs, rng, t_from=MID)
print("=== 4-MONTH v4.8, three engines ===")
print(f"HYBRID (tick fills + 1s exits): net {r['net']:+.2f} | "
      f"maxDD {r['max_dd']:+.2f} | {r['n']} cyc | {r['win_rate']*100:.0f}%")
print(f"  halves: Apr-May {a['net']:+.2f} | Jun-Jul {b['net']:+.2f}")
print("pure tick:  net +2906.17 | maxDD -403.73 | 615 cyc | 52%"
      "  (halves +1780.82 / +1125.35)")
print("pure 1s:    net +4374.06 | maxDD -340.92 | 641 cyc | 54%"
      "  (halves +2038.69 / +2335.37)", flush=True)

secs7 = tick_bars("data/ticks_aug7.npz")
rng7 = minute_ranges(secs7)
cfg7 = dict(BASE, hours={0, 1, 2, 3, 4, 5}, gate_series=make_gate(secs7),
            exit_on_sec_end=True)
t7 = int(datetime(2026, 8, 7, tzinfo=utc).timestamp())
r7 = run(cfg7, secs7, rng7, t_from=t7)
print(f"\n=== AUG 7 MORNING, hybrid: net {r7['net']:+.2f} | "
      f"{r7['n']} cycles ===")
for c in r7["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=utc)
    print(f"   end {d.strftime('%H:%M:%S')}  {c['outcome']:<11} "
          f"step {c['step']:.2f}  {c['pnl']:>+7.2f}")
print("\nDONE hybrid_engine_test")
