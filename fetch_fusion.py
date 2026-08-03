"""Download XAUUSD tick history from the Fusion Markets demo server."""
import os
from datetime import datetime, timezone

import numpy as np
import MetaTrader5 as mt5

START = datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc)   # ~4 months back
CHUNK = 500_000
SYMBOL = "XAUUSD"

mt5.initialize(login=426190, password="Kazmi@12345", server="FusionMarkets-Demo")
a = mt5.account_info()
print(f"Connected: {a.login} @ {a.server}")
mt5.symbol_select(SYMBOL, True)

all_chunks = []
frm = START
while True:
    ticks = mt5.copy_ticks_from(SYMBOL, frm, CHUNK, mt5.COPY_TICKS_ALL)
    if ticks is None:
        print("error:", mt5.last_error())
        break
    if len(ticks) == 0:
        break
    all_chunks.append(np.array(ticks))
    last = datetime.fromtimestamp(ticks[-1]["time"], tz=timezone.utc)
    print(f"  {len(ticks):>7,} ticks -> {last}")
    if len(ticks) < CHUNK:
        break
    frm = datetime.fromtimestamp(ticks[-1]["time_msc"] / 1000 + 0.001, tz=timezone.utc)

mt5.shutdown()

if all_chunks:
    data = np.concatenate(all_chunks)
    _, idx = np.unique(data["time_msc"], return_index=True)
    data = data[np.sort(idx)]
    os.makedirs("data", exist_ok=True)
    np.savez_compressed("data/ticks_fusion.npz", ticks=data)
    t0 = datetime.fromtimestamp(int(data[0]["time"]), tz=timezone.utc)
    t1 = datetime.fromtimestamp(int(data[-1]["time"]), tz=timezone.utc)
    print(f"\nSaved {len(data):,} ticks: {t0} -> {t1} "
          f"({os.path.getsize('data/ticks_fusion.npz') / 1e6:.1f} MB)")
else:
    print("No data returned.")
