"""Download XAUUSDm tick history from Exness into data/ticks.npz (numpy)."""
import os
from datetime import datetime, timezone

import numpy as np
import MetaTrader5 as mt5

import config as C

START = datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc)    # ~4 months back
CHUNK = 500_000

mt5.initialize(login=C.MT5_LOGIN, password=C.MT5_PASSWORD, server=C.MT5_SERVER)
mt5.symbol_select(C.SYMBOL, True)

all_chunks = []
frm = START
while True:
    ticks = mt5.copy_ticks_from(C.SYMBOL, frm, CHUNK, mt5.COPY_TICKS_ALL)
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
    # next chunk starts 1ms after the last tick we got
    frm = datetime.fromtimestamp(ticks[-1]["time_msc"] / 1000 + 0.001, tz=timezone.utc)

mt5.shutdown()

if all_chunks:
    data = np.concatenate(all_chunks)
    # dedupe on time_msc (chunk overlap safety)
    _, idx = np.unique(data["time_msc"], return_index=True)
    data = data[np.sort(idx)]
    os.makedirs("data", exist_ok=True)
    np.savez_compressed("data/ticks.npz", ticks=data)
    t0 = datetime.fromtimestamp(int(data[0]["time"]), tz=timezone.utc)
    t1 = datetime.fromtimestamp(int(data[-1]["time"]), tz=timezone.utc)
    print(f"\nSaved {len(data):,} ticks: {t0} -> {t1} ({os.path.getsize('data/ticks.npz') / 1e6:.1f} MB)")
else:
    print("No data.")
