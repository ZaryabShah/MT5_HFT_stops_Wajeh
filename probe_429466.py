"""READ-ONLY health check of the new Fusion demo 429466."""
from datetime import datetime, timezone

import MetaTrader5 as mt5

utc = timezone.utc
assert mt5.initialize(login=429466, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
acc = mt5.account_info()
mt5.symbol_select("XAUUSD", True)
import time
time.sleep(2)
tick = mt5.symbol_info_tick("XAUUSD")
srv = datetime.fromtimestamp(tick.time, tz=utc) if tick and tick.time else None
print(f"login {acc.login} @ {acc.server} | balance {acc.balance:.2f} | "
      f"equity {acc.equity:.2f} | margin {acc.margin:.2f}")
print(f"server clock: {srv}")

TP = {0: "buy", 1: "sell", 4: "buystop", 5: "sellstop"}
poss = mt5.positions_get() or []
orders = mt5.orders_get() or []
print(f"\nPOSITIONS ({len(poss)}):")
for p in poss:
    ts = datetime.fromtimestamp(p.time, tz=utc)
    print(f"  {ts.strftime('%m-%d %H:%M:%S')} {TP.get(p.type, p.type):<5} "
          f"{p.volume:.2f} @ {p.price_open:.2f}  P/L {p.profit:+.2f}  "
          f"magic {p.magic}  {p.comment}")
print(f"\nPENDING ({len(orders)}):")
for o in orders:
    print(f"  {TP.get(o.type, o.type):<9} {o.volume_current:.2f} @ "
          f"{o.price_open:.2f}  magic {o.magic}  {o.comment}")

deals = mt5.history_deals_get(datetime(2026, 8, 5, tzinfo=utc),
                              datetime(2026, 8, 8, tzinfo=utc)) or []
trade_deals = [d for d in deals if d.symbol]
print(f"\nDEALS since Aug 5 ({len(trade_deals)}):")
for d in trade_deals:
    ts = datetime.fromtimestamp(d.time, tz=utc)
    print(f"  {ts.strftime('%m-%d %H:%M:%S')} {TP.get(d.type, d.type):<5} "
          f"{d.volume:.2f} @ {d.price:.2f} profit {d.profit:+.2f} "
          f"comm {d.commission:+.2f} {d.comment}")
bal_deals = [d for d in deals if not d.symbol]
for d in bal_deals:
    ts = datetime.fromtimestamp(d.time, tz=utc)
    print(f"  {ts.strftime('%m-%d %H:%M:%S')} BALANCE {d.profit:+.2f}")
mt5.shutdown()
