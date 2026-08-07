"""NEW GRID ARCHITECTURES on the 4-month real feed (user mandate: more
v4.8-class machines from the movement style):
  RIDER   one-sided grid in the gate's trend direction (counter=0)
  ASYM    trend ladder 11 + counter ladder 3 (insurance)
  DBIAS   drift-biased grid in 00-06 (always long-tilted, counter=5)
  USWIDE  US session with session-scale steps (floor 2.0-3.0, cap 6-8)
All keep v4.8's exits/protections and pre-registered params."""
import numpy as np

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)

# signed 30-min direction per second (same construction as the gate)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
b = np.append(idx, len(t))
mcl = mid[b[1:] - 1]
pos = np.searchsorted(uniq, mins) - 1
lo = pos - 30
signed = mcl[np.clip(pos, 0, None)] - mcl[np.clip(lo, 0, None)]
DIR = np.where(signed >= 0, 1, -1).astype(np.int8)

V48 = dict(DEFAULT)
V48.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={20, 21, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))


def show(label, r):
    nd = r["net"] / -r["max_dd"] if r["max_dd"] < 0 else float("inf")
    print(f"{label:<34}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate'] * 100:>5.0f}%{nd:>7.1f}", flush=True)


print(f"{'variant':<34}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}{'net/DD':>7}")
show("v4.8 baseline (both ladders)", run(V48, secs, rng))
show("RIDER counter=0", run(dict(V48, dir_series=DIR, counter_levels=0),
                            secs, rng))
show("ASYM counter=3", run(dict(V48, dir_series=DIR, counter_levels=3),
                           secs, rng))
show("ASYM counter=5", run(dict(V48, dir_series=DIR, counter_levels=5),
                           secs, rng))
UP = np.ones(len(t), dtype=np.int8)
show("DBIAS 00-06 long-tilt c=5",
     run(dict(V48, hours={0, 1, 2, 3, 4, 5}, dir_series=UP,
              counter_levels=5), secs, rng))

US = {15, 16, 17, 18, 19}
for fl, cap in ((2.0, 6.0), (3.0, 8.0), (1.5, 5.0)):
    show(f"USWIDE fl{fl} cap{cap} gate",
         run(dict(V48, hours=US, step_floor=fl, step_cap=cap), secs, rng))
show("USWIDE fl2 cap6 NOgate",
     run(dict(V48, hours=US, step_floor=2.0, step_cap=6.0, gate_series=None),
         secs, rng))
print("\nDONE newgrids")
