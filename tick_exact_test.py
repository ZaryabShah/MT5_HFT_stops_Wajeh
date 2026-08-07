"""USER CHALLENGE: measure the REAL cost of 1-second OHLC aggregation vs the
true tick sequence. Feed the engine raw ticks (each tick = its own bar, so
fills follow the exact quote sequence — intra-second ordering resolved
perfectly) and compare with the standard 1s-bar run: full 4 months + halves,
then today's Aug 7 morning cycle-by-cycle."""
from datetime import datetime, timezone

import numpy as np

from backtest import DEFAULT, minute_ranges, run

utc = timezone.utc
MID = int(datetime(2026, 6, 1, tzinfo=utc).timestamp())


def tick_bars(npz):
    ticks = np.load(npz)["ticks"]
    t = ticks["time"].astype(np.int64)
    b = ticks["bid"].astype(np.float64)
    a = ticks["ask"].astype(np.float64)
    return dict(t=t, bid_o=b, bid_h=b, bid_l=b, bid_c=b,
                ask_o=a, ask_h=a, ask_l=a, ask_c=a)


def make_gate(secs):
    t = secs["t"].astype(np.int64)
    mid = (secs["bid_c"] + secs["ask_c"]) / 2
    mins = t // 60
    uniq, idx = np.unique(mins, return_index=True)
    bounds = np.append(idx, len(t))
    m_close = mid[bounds[1:] - 1]
    pref = np.cumsum(np.abs(np.diff(m_close, prepend=m_close[0])))
    pos = np.searchsorted(uniq, mins) - 1
    lo = pos - 30
    net = np.abs(m_close[np.clip(pos, 0, None)]
                 - m_close[np.clip(lo, 0, None)])
    tot = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
    er = np.where(tot > 1e-9, net / np.maximum(tot, 1e-9), 0.0)
    return (lo >= 0) & (er >= 0.25) & (net >= 3.0)


BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                 step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                 daily_stop=50))

if __name__ == "__main__":
    secs = tick_bars("data/ticks_fusion.npz")
    rng = minute_ranges(secs)
    cfg = dict(BASE, hours={20, 21, 0, 1, 2, 3, 4, 5},
               gate_series=make_gate(secs))
    r = run(cfg, secs, rng)
    a = run(cfg, secs, rng, t_to=MID)
    b = run(cfg, secs, rng, t_from=MID)
    print("=== 4-MONTH v4.8: TICK-EXACT vs 1s-bar ===")
    print(f"tick-exact: net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | "
          f"{r['n']} cyc | {r['win_rate']*100:.0f}%")
    print(f"  halves: Apr-May {a['net']:+.2f} | Jun-Jul {b['net']:+.2f}")
    print(f"1s-bar ref: net +4374.06 | maxDD -340.92 | 641 cyc | 54%")
    print(f"  halves: Apr-May +2038.69 | Jun-Jul +2335.37", flush=True)

    secs7 = tick_bars("data/ticks_aug7.npz")
    rng7 = minute_ranges(secs7)
    cfg7 = dict(BASE, hours={0, 1, 2, 3, 4, 5}, gate_series=make_gate(secs7))
    t7 = int(datetime(2026, 8, 7, tzinfo=utc).timestamp())
    r7 = run(cfg7, secs7, rng7, t_from=t7)
    print(f"\n=== AUG 7 MORNING: tick-exact replay ===")
    print(f"net {r7['net']:+.2f} | {r7['n']} cycles")
    for c in r7["cycles"]:
        d = datetime.fromtimestamp(int(c["t"]), tz=utc)
        print(f"   end {d.strftime('%H:%M:%S')}  {c['outcome']:<11} "
              f"step {c['step']:.2f}  {c['pnl']:>+7.2f}")
    print("\nDONE tick_exact_test")
