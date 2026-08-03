"""Parse the 1GB Fusion Markets tick CSV into data/ticks_fusion.npz, then run
the latest v4.2 config (cap 2.50, gate, purge 5, trail .5/.4, SL 6%) on the
REAL Fusion feed — both without breaker and with $50 — and print totals plus
a weekly table for cross-validation against the modeled numbers.

Note: CSV timestamps are Fusion SERVER time (typically UTC+2/3). Treated as-is;
shifts week boundaries by a couple of hours — irrelevant for totals.
"""
import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

CSV = "data/XAUUSD_202604021400_202607312358_FusionMarkets.csv"
NPZ = "data/ticks_fusion.npz"

if not os.path.exists(NPZ):
    print("parsing CSV (chunked)...")
    parts = []
    last_bid = last_ask = np.nan
    for i, ch in enumerate(pd.read_csv(
            CSV, sep="\t", skiprows=1, usecols=[0, 1, 2, 3],
            names=["date", "time", "bid", "ask"],
            dtype={"bid": float, "ask": float}, chunksize=2_000_000)):
        dt = pd.to_datetime(ch["date"] + " " + ch["time"],
                            format="%Y.%m.%d %H:%M:%S.%f", utc=True)
        epoch = dt.astype("int64") // 10**9
        bid = ch["bid"].to_numpy()
        ask = ch["ask"].to_numpy()
        # forward-fill missing sides (single-side tick updates), carrying
        # across chunk boundaries
        bs = pd.Series(np.concatenate([[last_bid], bid])).ffill().to_numpy()[1:]
        as_ = pd.Series(np.concatenate([[last_ask], ask])).ffill().to_numpy()[1:]
        last_bid, last_ask = bs[-1], as_[-1]
        arr = np.zeros(len(ch), dtype=[("time", "i8"), ("bid", "f8"), ("ask", "f8")])
        arr["time"] = epoch.to_numpy()
        arr["bid"] = bs
        arr["ask"] = as_
        parts.append(arr)
        print(f"  chunk {i + 1}: {sum(len(p) for p in parts):,} rows")
    ticks = np.concatenate(parts)
    ticks = ticks[~(np.isnan(ticks["bid"]) | np.isnan(ticks["ask"]))]
    np.savez_compressed(NPZ, ticks=ticks)
    print(f"saved {len(ticks):,} ticks -> {NPZ}")

from backtest import DEFAULT, build_seconds, minute_ranges, run  # noqa: E402

secs = build_seconds(NPZ, "data/secs_fusion.npz")
rng = minute_ranges(secs)
t0, t1 = int(secs["t"][0]), int(secs["t"][-1])
spread = float(np.mean(secs["ask_c"] - secs["bid_c"]))
print(f"\nREAL Fusion feed: {datetime.fromtimestamp(t0, tz=timezone.utc):%Y-%m-%d} "
      f"-> {datetime.fromtimestamp(t1, tz=timezone.utc):%Y-%m-%d} (server time), "
      f"{len(secs['t']):,} seconds, avg spread ${spread:.3f}")

BASE = dict(DEFAULT)
BASE.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                 purge_at=5, step_cap=2.5, regime_mult=4.0,
                 commission_per_lot_side=2.25))

for label, L in [("NO breaker (finalized config)", None), ("$50 breaker", 50)]:
    r = run(dict(BASE, daily_stop=L), secs, rng)
    bal = 1000.0
    low = 1000.0
    blown = None
    weeks = {}
    for c in r["cycles"]:
        bal += c["pnl"]
        low = min(low, bal)
        if blown is None and bal <= 30:
            blown = c["t"]
        d = datetime.fromtimestamp(c["t"], tz=timezone.utc)
        monday = (d - timedelta(days=d.weekday())).strftime("%m-%d")
        weeks.setdefault(monday, []).append((bal, c["pnl"]))
    print(f"\n===== {label} — REAL Fusion data =====")
    print(f"net {r['net']:+.2f} | maxDD {r['max_dd']:+.2f} | {r['n']} cycles | "
          f"{r['win_rate']*100:.0f}% wins | lowest from $1k: {low:.2f}"
          + (f" | BLEW UP {datetime.fromtimestamp(blown, tz=timezone.utc):%m-%d}"
             if blown else " | survived"))
    print(f"{'week':<8}{'start':>9}{'end':>9}{'lowest':>9}{'net':>9}")
    prev = 1000.0
    for wk in sorted(weeks):
        rows = weeks[wk]
        end = rows[-1][0]
        lowest = min(prev, min(b for b, _ in rows))
        net = sum(p for _, p in rows)
        print(f"{wk:<8}{prev:>9.2f}{end:>9.2f}{lowest:>9.2f}{net:>+9.2f}")
        prev = end
