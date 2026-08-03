"""Tick-replay backtester for the Wajeh grid bot (v4.1 logic).

Aggregates recorded ticks to 1-second bars (bid/ask OHLC) and replays the
exact cycle logic: adaptive capped step, 11+11 stop grid, trend purge, basket
trail, pair cap, equity stop, 12%-at-last-stop target, last-stop close,
30s re-anchor gap. Fixed test lot, virtual-basis targets — same math as bot.py.

Known simplifications (documented, deliberate):
- 1-second resolution (live bot polls at 0.5s) — comparable granularity
- stop fills at level price, or at second-open on gap-through (includes gap
  slippage, excludes queue slippage)
- no commission by default (Exness Standard); pass commission_per_lot_side
  to model ECN accounts
"""
import os
from datetime import datetime, timezone

import numpy as np

DATA = "data/ticks.npz"
SECS_CACHE = "data/secs.npz"

DEFAULT = dict(
    lot=0.01,
    levels=11,
    target_level=11,          # 12% lands at the LAST stop (user spec 08-01)
    target_pct=0.12,
    sl_pct=0.08,
    pair_cap=3,
    purge_at=4,
    purge_max_other=2,
    trail_arm=0.5,
    trail_giveback=0.3,
    step_mult=0.5,
    step_floor=0.30,
    step_cap=0.90,
    regime_mult=None,         # None = trade everything; e.g. 4.0 = v4 gate
    respawn_gap=30,           # seconds between cycles
    commission_per_lot_side=0.0,
    contract=100.0,
    max_spread=0.35,          # skip cycle starts when spread is abnormal
    daily_stop=None,          # stop trading until next UTC day once the day's
                              # realized P/L reaches -this many dollars
    trigger_on_mid=False,     # True: levels trigger on MID crossing (virtual
                              # stops) instead of ask/bid touch — immune to
                              # spread-spike phantom fills; pays half-spread
    hours=None,               # set of allowed UTC hours for cycle STARTS
                              # (None = trade around the clock)
    gate_series=None,         # optional bool array aligned to secs: cycle may
)                             # only START where True (regime classifiers)


def build_seconds(data=DATA, cache=SECS_CACHE):
    """Aggregate raw ticks to per-second bid/ask OHLC (cached)."""
    if os.path.exists(cache):
        z = np.load(cache)
        return {k: z[k] for k in z.files}
    ticks = np.load(data)["ticks"]
    ticks = ticks[(ticks["bid"] > 0) & (ticks["ask"] > 0)]
    sec = ticks["time"].astype(np.int64)
    uniq, start_idx = np.unique(sec, return_index=True)
    out = dict(
        t=uniq,
        bid_o=np.empty(len(uniq)), bid_h=np.empty(len(uniq)),
        bid_l=np.empty(len(uniq)), bid_c=np.empty(len(uniq)),
        ask_o=np.empty(len(uniq)), ask_h=np.empty(len(uniq)),
        ask_l=np.empty(len(uniq)), ask_c=np.empty(len(uniq)),
    )
    bounds = np.append(start_idx, len(ticks))
    for i in range(len(uniq)):
        b = ticks["bid"][bounds[i]:bounds[i + 1]]
        a = ticks["ask"][bounds[i]:bounds[i + 1]]
        out["bid_o"][i], out["bid_h"][i], out["bid_l"][i], out["bid_c"][i] = b[0], b.max(), b.min(), b[-1]
        out["ask_o"][i], out["ask_h"][i], out["ask_l"][i], out["ask_c"][i] = a[0], a.max(), a.min(), a[-1]
    np.savez_compressed(cache, **out)
    return out


def minute_ranges(secs):
    """minute -> bid high-low range, for the adaptive step."""
    mins = secs["t"] // 60
    uniq, idx = np.unique(mins, return_index=True)
    bounds = np.append(idx, len(mins))
    rng = {}
    for i, m in enumerate(uniq):
        hi = secs["bid_h"][bounds[i]:bounds[i + 1]].max()
        lo = secs["bid_l"][bounds[i]:bounds[i + 1]].min()
        rng[int(m)] = hi - lo
    return rng


def adaptive_step(rng, t, cfg):
    """Average range of the last 5 closed minutes before timestamp t."""
    m = int(t // 60)
    vals = [rng[m - k] for k in range(1, 6) if (m - k) in rng]
    if not vals:
        return cfg["step_floor"]
    step = cfg["step_mult"] * (sum(vals) / len(vals))
    step = max(cfg["step_floor"], step)
    if cfg["step_cap"]:
        step = min(step, cfg["step_cap"])
    return round(step, 3)


def raw_step(rng, t, cfg):
    m = int(t // 60)
    vals = [rng[m - k] for k in range(1, 6) if (m - k) in rng]
    return max(cfg["step_floor"], cfg["step_mult"] * (sum(vals) / len(vals))) if vals else cfg["step_floor"]


def run(cfg, secs, rng, t_from=None, t_to=None):
    """Replay. Returns dict with cycles, net, max drawdown, equity curve."""
    t = secs["t"]
    lo = np.searchsorted(t, t_from) if t_from else 0
    hi = np.searchsorted(t, t_to) if t_to else len(t)
    C_ = cfg["contract"]
    lot = cfg["lot"]
    comm = cfg["commission_per_lot_side"] * lot

    cycles = []
    equity = 0.0            # cumulative realized
    peak_eq = 0.0
    max_dd = 0.0
    cur_day = -1
    day_pnl = 0.0

    i = lo
    idle_until = 0
    while i < hi:
        ts = t[i]
        if ts < idle_until:
            i += 1
            continue
        if cfg.get("hours") is not None and int(ts // 3600) % 24 not in cfg["hours"]:
            i += 1
            continue
        if cfg.get("gate_series") is not None and not cfg["gate_series"][i]:
            i += 1
            continue
        spread = secs["ask_c"][i] - secs["bid_c"][i]
        if cfg["max_spread"] and spread > cfg["max_spread"]:
            i += 1
            continue
        # regime gate (v4) — optional
        if cfg["regime_mult"]:
            if raw_step(rng, ts, cfg) < cfg["regime_mult"] * spread:
                i += 1
                continue
        # ---- start cycle ----
        step = adaptive_step(rng, ts, cfg)
        n = cfg["target_level"]
        basis = lot * C_ * step * n * (n - 1) / 2 / cfg["target_pct"]
        target = basis * cfg["target_pct"]
        maxloss = basis * cfg["sl_pct"]
        anchor_a, anchor_b = secs["ask_c"][i], secs["bid_c"][i]
        buys = [round(anchor_a + k * step, 3) for k in range(1, cfg["levels"] + 1)]
        sells = [round(anchor_b - k * step, 3) for k in range(1, cfg["levels"] + 1)]
        longs, shorts = [], []          # entry prices
        realized = 0.0
        purged = False
        peak = 0.0
        outcome = None
        j = i + 1
        while j < hi:
            ah, bl = secs["ask_h"][j], secs["bid_l"][j]
            ao, bo = secs["ask_o"][j], secs["bid_o"][j]
            bc, ac = secs["bid_c"][j], secs["ask_c"][j]
            # trigger pending stops (gap-through fills at second open)
            if cfg.get("trigger_on_mid"):
                mh = (ah + secs["bid_h"][j]) / 2
                ml = (bl + secs["ask_l"][j]) / 2
                mo = (ao + bo) / 2
                half = (secs["ask_c"][j] - secs["bid_c"][j]) / 2
                while buys and mh >= buys[0]:
                    longs.append(max(buys.pop(0), mo) + half)
                    realized -= comm
                while sells and ml <= sells[0]:
                    shorts.append(min(sells.pop(0), mo) - half)
                    realized -= comm
            else:
                while buys and ah >= buys[0]:
                    longs.append(max(buys.pop(0), ao))
                    realized -= comm
                while sells and bl <= sells[0]:
                    shorts.append(min(sells.pop(0), bo))
                    realized -= comm
            # mark to market
            profit = realized \
                + sum((bc - e) for e in longs) * C_ * lot \
                + sum((e - ac) for e in shorts) * C_ * lot
            peak = max(peak, profit)
            if profit >= target:
                outcome = "target"
            elif peak >= target * cfg["trail_arm"] and \
                    profit <= peak - target * cfg["trail_giveback"]:
                outcome = "trail"
            else:
                if not purged and cfg["purge_at"]:
                    if len(longs) >= cfg["purge_at"] and len(shorts) <= cfg["purge_max_other"]:
                        realized += sum((e - ac) for e in shorts) * C_ * lot - comm * len(shorts)
                        shorts, sells, purged = [], [], True
                    elif len(shorts) >= cfg["purge_at"] and len(longs) <= cfg["purge_max_other"]:
                        realized += sum((bc - e) for e in longs) * C_ * lot - comm * len(longs)
                        longs, buys, purged = [], [], True
                if outcome is None and profit <= -maxloss:
                    outcome = "equitystop"
                elif outcome is None and cfg["pair_cap"] and \
                        min(len(longs), len(shorts)) >= cfg["pair_cap"]:
                    outcome = "paircap"
                elif outcome is None and not buys and not sells and (longs or shorts):
                    outcome = "all_filled"
            if outcome:
                pnl = realized \
                    + sum((bc - e) for e in longs) * C_ * lot \
                    + sum((e - ac) for e in shorts) * C_ * lot \
                    - comm * (len(longs) + len(shorts))
                cycles.append(dict(t=int(t[j]), outcome=outcome, pnl=pnl,
                                   step=step, basis=basis, pct=pnl / basis))
                equity += pnl
                peak_eq = max(peak_eq, equity)
                max_dd = min(max_dd, equity - peak_eq)
                idle_until = t[j] + cfg["respawn_gap"]
                day = int(t[j]) // 86400
                if day != cur_day:
                    cur_day, day_pnl = day, 0.0
                day_pnl += pnl
                if cfg.get("daily_stop") and day_pnl <= -cfg["daily_stop"]:
                    idle_until = (day + 1) * 86400
                i = j
                break
            j += 1
        else:
            break
        i += 1

    wins = [c for c in cycles if c["pnl"] > 0]
    return dict(cycles=cycles, net=equity, max_dd=max_dd,
                n=len(cycles), wins=len(wins),
                win_rate=len(wins) / len(cycles) if cycles else 0.0)


def fmt_ts(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%m-%d %H:%M")


if __name__ == "__main__":
    print("Building 1-second bars (first run takes a minute)...")
    secs = build_seconds()
    rng = minute_ranges(secs)
    print(f"{len(secs['t']):,} seconds of market data "
          f"({fmt_ts(secs['t'][0])} -> {fmt_ts(secs['t'][-1])} UTC)")

    # Validation: v4.1 config over the exact live window (Fri 17:00 UTC -> close)
    v41_from = int(datetime(2026, 7, 31, 17, 0, tzinfo=timezone.utc).timestamp())
    res = run(DEFAULT, secs, rng, t_from=v41_from)
    print(f"\n--- validation: v4.1 config, Fri 17:00 UTC -> close "
          f"(live actual: 6 cycles, +$26.93) ---")
    for c in res["cycles"]:
        print(f"  {fmt_ts(c['t'])}  {c['outcome']:<11} step {c['step']:.2f}  "
              f"{c['pnl']:+7.2f}  ({c['pct']*100:+.1f}%)")
    print(f"net {res['net']:+.2f} | {res['wins']}W/{res['n']-res['wins']}L | "
          f"maxDD {res['max_dd']:.2f}")
