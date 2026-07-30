"""Diagnostic: current account state + today's deal/order history."""
from datetime import datetime, timedelta

import MetaTrader5 as mt5

import config as C

if not mt5.initialize(login=C.MT5_LOGIN, password=C.MT5_PASSWORD, server=C.MT5_SERVER):
    print("init failed:", mt5.last_error())
    raise SystemExit

acc = mt5.account_info()
print(f"Balance {acc.balance} | Equity {acc.equity} | Margin {acc.margin} | Free {acc.margin_free}")
print(f"Open positions: {len(mt5.positions_get(symbol=C.SYMBOL) or [])}")
print(f"Pending orders: {len(mt5.orders_get(symbol=C.SYMBOL) or [])}")

now = datetime.now()
frm = now - timedelta(hours=2)
deals = mt5.history_deals_get(frm, now + timedelta(hours=1)) or []
print(f"\nDeals last 2h: {len(deals)}")
total = 0.0
for d in deals:
    if d.symbol != C.SYMBOL and d.symbol:
        continue
    t = datetime.fromtimestamp(d.time)
    kind = {0: "BUY", 1: "SELL"}.get(d.type, str(d.type))
    total += d.profit + d.commission + d.swap + getattr(d, "fee", 0.0)
    print(f"  {t:%H:%M:%S} {kind:>4} {d.volume} @ {d.price} | profit {d.profit:+.2f} "
          f"comm {d.commission:+.2f} | {d.comment}")
print(f"Net P/L of listed deals: {total:+.2f}")

mt5.shutdown()
