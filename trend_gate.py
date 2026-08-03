"""Trend-classifier gate for v4.6: only start cycles when the market is
measurably TRENDING. Classifier = Kaufman efficiency ratio over the last N
minutes (|net move| / sum |minute moves|), plus a net-move variant.
Sweep on the real Fusion feed, 4 months."""
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

V46 = dict(DEFAULT)
V46.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3,
                purge_at=5, step_cap=2.5, regime_mult=6.0,
                commission_per_lot_side=2.25, daily_stop=50,
                hours={22, 23, 0, 1, 2, 3, 4, 5}))

secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
rng = minute_ranges(secs)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2

# minute closes (last mid of each minute) + prefix sum of |minute-to-minute|
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
bounds = np.append(idx, len(t))
m_close = mid[bounds[1:] - 1]
m_absdiff = np.abs(np.diff(m_close, prepend=m_close[0]))
pref = np.cumsum(m_absdiff)
# map each second to its minute's position
sec_minpos = np.searchsorted(uniq, mins)


def er_series(lookback_min, thresh):
    """Boolean per-second: efficiency ratio over last N CLOSED minutes >= thresh."""
    pos = sec_minpos - 1                       # last closed minute
    lo = pos - lookback_min
    ok = lo >= 0
    net = np.abs(m_close[np.clip(pos, 0, None)] - m_close[np.clip(lo, 0, None)])
    total = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
    er = np.where(total > 1e-9, net / np.maximum(total, 1e-9), 0.0)
    return ok & (er >= thresh)


def move_series(lookback_min, thresh):
    """Boolean: |net move over last N closed minutes| >= thresh dollars."""
    pos = sec_minpos - 1
    lo = pos - lookback_min
    ok = lo >= 0
    net = np.abs(m_close[np.clip(pos, 0, None)] - m_close[np.clip(lo, 0, None)])
    return ok & (net >= thresh)


if __name__ == "__main__":
    base = run(V46, secs, rng)
    print(f"v4.6 baseline: net {base['net']:+.2f} | maxDD {base['max_dd']:+.2f} | "
          f"{base['n']} cyc | {base['win_rate']*100:.0f}%\n")

    print(f"{'gate':<24}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}")
    for lb in (15, 30, 60):
        for th in (0.25, 0.35, 0.45):
            r = run(dict(V46, gate_series=er_series(lb, th)), secs, rng)
            print(f"ER({lb:>2}m) >= {th:<10}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}"
                  f"{r['n']:>6}{r['win_rate']*100:>5.0f}%")
    for lb, th in ((30, 2.0), (30, 3.0), (60, 4.0)):
        r = run(dict(V46, gate_series=move_series(lb, th)), secs, rng)
        print(f"|move {lb}m| >= ${th:<7}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}"
              f"{r['n']:>6}{r['win_rate']*100:>5.0f}%")
