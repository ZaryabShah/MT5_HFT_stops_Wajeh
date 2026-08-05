"""v4.8 re-scaled onto BTCUSD / EURUSD / USDJPY (real Fusion feeds).
All gold-dollar magic numbers re-expressed in per-symbol units:
  step floor/cap, trend move-min  -> scaled by median 1-min range ratio
  max_spread gate                 -> 4x the symbol's own avg spread
  daily breaker                   -> 36% of the floor-step basis (gold ratio)
Percent rules (12% target @L11, 8% SL, trail, purge, pair cap, ER>=0.25,
6x spread regime, hours 20-22U00-06 server) transfer unchanged.
Commission: EUR 2.25/side/lot, JPY ¥363/side/lot (=$4.50 RT), BTC zero.
Contract: EUR/JPY 100k, BTC 1.0. JPY results converted at median USDJPY.
"""
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

GOLD_MED_RANGE = None  # filled from gold cache


def gate_arrays(secs, move_min):
    t = secs["t"].astype(np.int64)
    mid = (secs["bid_c"] + secs["ask_c"]) / 2
    mins = t // 60
    uniq, idx = np.unique(mins, return_index=True)
    bounds = np.append(idx, len(t))
    m_close = mid[bounds[1:] - 1]
    pref = np.cumsum(np.abs(np.diff(m_close, prepend=m_close[0])))
    pos = np.searchsorted(uniq, mins) - 1
    lo = pos - 30
    ok = lo >= 0
    net = np.abs(m_close[np.clip(pos, 0, None)] - m_close[np.clip(lo, 0, None)])
    tot = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
    er = np.where(tot > 1e-12, net / np.maximum(tot, 1e-12), 0.0)
    return ok & (er >= 0.25) & (net >= move_min)


def med_range(rng):
    v = np.array(list(rng.values()))
    return float(np.median(v[v > 0]))


# gold reference
gsecs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
GOLD_MED_RANGE = med_range(minute_ranges(gsecs))
print(f"gold median 1-min range: {GOLD_MED_RANGE:.4f}")
del gsecs

JOBS = [
    ("EURUSD", "data/ticks_eur.npz", "data/secs_eur.npz", 100000.0, 2.25, 1.0, 5),
    ("USDJPY", "data/ticks_jpy.npz", "data/secs_jpy.npz", 100000.0, 363.0, None, 3),
]

for sym, npz, cache, contract, comm, usd, digits in JOBS:
    secs = build_seconds(npz, cache)
    rng = minute_ranges(secs)
    mr = med_range(rng)
    k = mr / GOLD_MED_RANGE
    spread = float(np.mean(secs["ask_c"] - secs["bid_c"]))
    mid = float(np.median((secs["bid_c"] + secs["ask_c"]) / 2))
    conv = (1.0 / mid) if usd is None else usd    # JPY -> USD
    floor_, cap_, move_ = 0.30 * k, 2.50 * k, 3.0 * k
    basis_floor = 0.01 * contract * floor_ * 55 / 0.12
    breaker = 0.36 * basis_floor
    print(f"\n=== {sym}: med 1-min range {mr:.5f} (k={k:.4f}) | avg spread "
          f"{spread:.5f} | floor {floor_:.5f} cap {cap_:.5f} move {move_:.5f} "
          f"| breaker {breaker:.2f} (quote units)")
    gate = gate_arrays(secs, move_)
    cfg = dict(DEFAULT)
    cfg.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                    step_mult=0.5, step_floor=floor_, step_cap=cap_,
                    regime_mult=6.0, commission_per_lot_side=comm,
                    contract=contract, max_spread=4 * spread, digits=digits,
                    daily_stop=breaker, gate_series=gate))
    for wl, hrs in (("20-22U00-06", {20, 21, 0, 1, 2, 3, 4, 5}), ("24h", None)):
        r = run(dict(cfg, hours=hrs), secs, rng)
        nd = r["net"] / -r["max_dd"] if r["max_dd"] < 0 else float("inf")
        print(f"  {wl:<13} net {r['net'] * conv:>+10.2f} USD | "
              f"maxDD {r['max_dd'] * conv:>+9.2f} | {r['n']:>4} cyc | "
              f"{r['win_rate'] * 100:.0f}% | net/DD {nd:.1f}", flush=True)
    del secs, rng, gate
print("\nDONE symbol_v48")
