"""Fetch as much XAUUSD H1 (and D1) bar history as Fusion serves."""
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

utc = timezone.utc
assert mt5.initialize(login=429466, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
mt5.symbol_select("XAUUSD", True)
for tf, name in ((mt5.TIMEFRAME_H1, "h1"), (mt5.TIMEFRAME_D1, "d1")):
    r = mt5.copy_rates_range("XAUUSD", tf,
                             datetime(2010, 1, 1, tzinfo=utc),
                             datetime(2026, 8, 7, tzinfo=utc))
    if r is None or len(r) == 0:
        print(f"{name}: nothing")
        continue
    arr = np.array(r)
    np.save(f"data/xau_{name}.npy", arr)
    a = datetime.fromtimestamp(int(arr['time'][0]), tz=utc)
    z = datetime.fromtimestamp(int(arr['time'][-1]), tz=utc)
    print(f"{name}: {len(arr):,} bars | {a:%Y-%m-%d} -> {z:%Y-%m-%d}")
mt5.shutdown()
