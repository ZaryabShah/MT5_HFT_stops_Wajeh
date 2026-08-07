"""Measure whether Python-level parallelism speeds up MT5 order placement.
Places 22 pending stops FAR from market ($50-72 away, magic 999777, 0.01
lot) three ways — serial, 8 threads, 16 threads — timing each, deleting all
between rounds. Safe: far pendings can't fill, distinct magic, bot idle."""
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import MetaTrader5 as mt5

MAGIC = 999777
assert mt5.initialize(login=429466, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
time.sleep(2)
tick = mt5.symbol_info_tick("XAUUSD")
print(f"server clock: {datetime.fromtimestamp(tick.time, tz=timezone.utc)}"
      f"  bid {tick.bid:.2f} ask {tick.ask:.2f}")


def req(kind, price):
    return {"action": mt5.TRADE_ACTION_PENDING, "symbol": "XAUUSD",
            "volume": 0.01, "type": kind, "price": round(price, 2),
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC, "magic": MAGIC,
            "comment": "timing-test"}


def ladder():
    tk = mt5.symbol_info_tick("XAUUSD")
    return ([req(mt5.ORDER_TYPE_BUY_STOP, tk.ask + 50 + 2 * k)
             for k in range(11)]
            + [req(mt5.ORDER_TYPE_SELL_STOP, tk.bid - 50 - 2 * k)
               for k in range(11)])


def cleanup():
    for o in (mt5.orders_get(symbol="XAUUSD") or []):
        if o.magic == MAGIC:
            mt5.order_send({"action": mt5.TRADE_ACTION_REMOVE,
                            "order": o.ticket})


def report(label, t0, t1, results):
    ok = sum(1 for r in results if r and r.retcode == mt5.TRADE_RETCODE_DONE)
    dt = t1 - t0
    print(f"{label:<14} {ok}/22 placed in {dt:6.2f}s "
          f"({1000 * dt / 22:6.0f} ms/order, {22 / dt:5.1f} orders/s)",
          flush=True)


cleanup()
for label, workers in (("serial", 0), ("8 threads", 8), ("16 threads", 16)):
    reqs = ladder()
    t0 = time.perf_counter()
    if workers == 0:
        res = [mt5.order_send(r) for r in reqs]
    else:
        with ThreadPoolExecutor(workers) as ex:
            res = list(ex.map(mt5.order_send, reqs))
    t1 = time.perf_counter()
    report(label, t0, t1, res)
    cleanup()
    time.sleep(1)

left = [o for o in (mt5.orders_get(symbol="XAUUSD") or [])
        if o.magic == MAGIC]
print(f"cleanup check: {len(left)} test orders left (must be 0)")
mt5.shutdown()
