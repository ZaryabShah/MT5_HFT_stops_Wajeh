"""Probe how much tick and bar history the Fusion demo server serves."""
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5

mt5.initialize(login=426190, password="Kazmi@12345", server="FusionMarkets-Demo")
mt5.symbol_select("XAUUSD", True)
time.sleep(2)

for d in [datetime(2026, 7, 30, tzinfo=timezone.utc),
          datetime(2026, 7, 20, tzinfo=timezone.utc),
          datetime(2026, 7, 1, tzinfo=timezone.utc),
          datetime(2026, 6, 1, tzinfo=timezone.utc),
          datetime(2026, 4, 1, tzinfo=timezone.utc)]:
    t = mt5.copy_ticks_from("XAUUSD", d, 1000, mt5.COPY_TICKS_ALL)
    n = len(t) if t is not None else -1
    first = (datetime.fromtimestamp(t[0]["time"], tz=timezone.utc)
             if t is not None and len(t) else None)
    print(f"{d:%Y-%m-%d}: {n} ticks, first={first}, err={mt5.last_error()}")

r = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M1, 0, 99999)
oldest = (datetime.fromtimestamp(int(r[0]["time"]), tz=timezone.utc)
          if r is not None and len(r) else None)
print(f"M1 bars available: {len(r) if r is not None else 0}, oldest: {oldest}")
mt5.shutdown()
