"""Parse the user's other Fusion CSV exports (BTCUSD, EURUSD, USDJPY) into
tick npz + second-bar caches. Same format as the XAUUSD export."""
import os

import numpy as np
import pandas as pd

from backtest import build_seconds

JOBS = [
    ("data/EURUSD_202603300002_202607312358.csv", "data/ticks_eur.npz", "data/secs_eur.npz"),
    ("data/USDJPY_202605220627_202607312358.csv", "data/ticks_jpy.npz", "data/secs_jpy.npz"),
    ("data/BTCUSD_202603290455_202608011856.csv", "data/ticks_btc.npz", "data/secs_btc.npz"),
]

for csv, npz, cache in JOBS:
    if not os.path.exists(npz):
        print(f"parsing {csv} ...", flush=True)
        parts = []
        last_bid = last_ask = np.nan
        for i, ch in enumerate(pd.read_csv(
                csv, sep="\t", skiprows=1, usecols=[0, 1, 2, 3],
                names=["date", "time", "bid", "ask"],
                dtype={"bid": float, "ask": float}, chunksize=2_000_000)):
            dt = pd.to_datetime(ch["date"] + " " + ch["time"],
                                format="%Y.%m.%d %H:%M:%S.%f", utc=True)
            epoch = dt.astype("int64") // 10**9
            bid = ch["bid"].to_numpy()
            ask = ch["ask"].to_numpy()
            bs = pd.Series(np.concatenate([[last_bid], bid])).ffill().to_numpy()[1:]
            as_ = pd.Series(np.concatenate([[last_ask], ask])).ffill().to_numpy()[1:]
            last_bid, last_ask = bs[-1], as_[-1]
            arr = np.zeros(len(ch), dtype=[("time", "i8"), ("bid", "f8"), ("ask", "f8")])
            arr["time"] = epoch.to_numpy()
            arr["bid"] = bs
            arr["ask"] = as_
            parts.append(arr)
            if (i + 1) % 5 == 0:
                print(f"  chunk {i + 1}: {sum(len(p) for p in parts):,} rows", flush=True)
        ticks = np.concatenate(parts)
        ticks = ticks[~(np.isnan(ticks["bid"]) | np.isnan(ticks["ask"]))]
        np.savez_compressed(npz, ticks=ticks)
        print(f"saved {len(ticks):,} ticks -> {npz}", flush=True)
        del parts, ticks
    print(f"building second bars for {npz} ...", flush=True)
    secs = build_seconds(npz, cache)
    sp = float(np.mean(secs["ask_c"] - secs["bid_c"]))
    mid = float(np.median((secs["bid_c"] + secs["ask_c"]) / 2))
    print(f"  {len(secs['t']):,} seconds | median mid {mid:.5f} | "
          f"avg spread {sp:.5f} ({sp / mid * 1e4:.2f} bp)", flush=True)
    del secs
print("\nDONE parse_symbols")
