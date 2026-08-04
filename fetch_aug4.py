"""Try to get Aug 3-5 data from the Fusion demo: ticks if the API serves
them, M1 rates as fallback. Times = server basis throughout."""
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

assert mt5.initialize(login=426190, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
print("connected:", mt5.account_info().server)
assert mt5.symbol_select("XAUUSD", True)

utc = timezone.utc
frm = datetime(2026, 8, 3, tzinfo=utc)
to = datetime(2026, 8, 5, 12, tzinfo=utc)

ticks = mt5.copy_ticks_range("XAUUSD", frm, to, mt5.COPY_TICKS_ALL)
n = 0 if ticks is None else len(ticks)
print(f"ticks Aug 3-5: {n:,}")
if n:
    arr = np.array(ticks)
    np.savez_compressed("data/ticks_aug.npz", ticks=arr)
    t0 = datetime.fromtimestamp(int(arr['time'][0]), tz=utc)
    t1 = datetime.fromtimestamp(int(arr['time'][-1]), tz=utc)
    print(f"  range: {t0} -> {t1} (server)")

rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M1, frm, to)
print(f"M1 bars Aug 3-5: {0 if rates is None else len(rates):,}")
if rates is not None and len(rates):
    np.save("data/m1_aug.npy", np.array(rates))
    r0 = datetime.fromtimestamp(int(rates[0]['time']), tz=utc)
    r1 = datetime.fromtimestamp(int(rates[-1]['time']), tz=utc)
    print(f"  range: {r0} -> {r1} (server)")
mt5.shutdown()
