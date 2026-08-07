"""Reconstruct live cycle 7/8 (Aug 7, 03:40-04:30 server) from the broker's
order history, and compute what the replay's cycle-7 ladder looked like
(anchor second, price, adaptive step) for a side-by-side comparison."""
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

from backtest import adaptive_step, build_seconds, minute_ranges

utc = timezone.utc
OT = {0: "BUY", 1: "SELL", 2: "BUYLIM", 3: "SELLLIM", 4: "BUYSTOP",
      5: "SELLSTOP"}

assert mt5.initialize(login=429466, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
time.sleep(2)
lo = datetime(2026, 8, 7, 3, 39, tzinfo=utc)
hi = datetime(2026, 8, 7, 4, 40, tzinfo=utc)
mt5.history_orders_get(lo, hi)
time.sleep(1)
orders = mt5.history_orders_get(lo, hi) or []
deals = mt5.history_deals_get(lo, hi) or []
mt5.shutdown()

print("=== LIVE ORDERS placed 03:39-04:40 ===")
for o in sorted(orders, key=lambda x: x.time_setup):
    ts = datetime.fromtimestamp(o.time_setup, tz=utc).strftime("%H:%M:%S")
    print(f"  {ts}  {OT.get(o.type, o.type):<8} {o.volume_initial:.2f} "
          f"@ {o.price_open:.2f}  state={o.state}")

print("\n=== LIVE ENTRY FILLS (deals, entry=in) ===")
for d in sorted(deals, key=lambda x: x.time):
    if d.entry == 0 and abs(d.volume) > 0:
        ts = datetime.fromtimestamp(d.time, tz=utc).strftime("%H:%M:%S")
        kind = "BUY " if d.type == 0 else "SELL"
        print(f"  {ts}  {kind} {d.volume:.2f} @ {d.price:.2f}")

secs = build_seconds("data/ticks_aug7.npz", "data/secs_aug7.npz")
rng = minute_ranges(secs)
t = secs["t"].astype(np.int64)
CFG = dict(step_mult=0.5, step_floor=0.30, step_cap=2.5)
print("\n=== REPLAY-SIDE VIEW (per-second quotes + step by anchor time) ===")
for hh, mm, ss in ((3, 40, 44), (3, 41, 0), (3, 41, 30), (3, 42, 0),
                   (4, 1, 20), (4, 2, 0)):
    ts = int(datetime(2026, 8, 7, hh, mm, ss, tzinfo=utc).timestamp())
    j = np.searchsorted(t, ts, "right") - 1
    st = adaptive_step(rng, ts, CFG)
    print(f"  {hh:02d}:{mm:02d}:{ss:02d}  bid {secs['bid_c'][j]:.2f} "
          f"ask {secs['ask_c'][j]:.2f}  adaptive step -> {st:.2f}")
print("\nprice path 03:40 -> 04:45 (1-min mids):")
for k in range(0, 66, 5):
    ts = int(datetime(2026, 8, 7, 3, 40, tzinfo=utc).timestamp()) + k * 60
    j = np.searchsorted(t, ts, "right") - 1
    m = (secs["bid_c"][j] + secs["ask_c"][j]) / 2
    d = datetime.fromtimestamp(int(t[j]), tz=utc)
    print(f"  {d.strftime('%H:%M')}  {m:.2f}")
