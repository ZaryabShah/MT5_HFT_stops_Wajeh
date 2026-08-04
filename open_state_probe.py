"""READ-ONLY: details of the open positions/pendings on the Fusion demo."""
from datetime import datetime, timezone

import MetaTrader5 as mt5

assert mt5.initialize(login=426190, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
utc = timezone.utc
acc = mt5.account_info()
tick = mt5.symbol_info_tick("XAUUSD")
srv = datetime.fromtimestamp(tick.time, tz=utc) if tick and tick.time else None
print(f"balance {acc.balance:.2f} | equity {acc.equity:.2f} | "
      f"margin {acc.margin:.2f} | server clock now: {srv}")

TYPES = {0: "buy", 1: "sell", 4: "buystop", 5: "sellstop"}
print("\nOPEN POSITIONS:")
for p in mt5.positions_get() or []:
    ts = datetime.fromtimestamp(p.time, tz=utc)
    print(f"  {ts.strftime('%m-%d %H:%M:%S')} {TYPES.get(p.type, p.type):<5} "
          f"{p.volume:.2f} @ {p.price_open:.2f}  P/L {p.profit:+.2f}  "
          f"magic {p.magic}  {p.comment}")

print("\nPENDING ORDERS:")
for o in mt5.orders_get() or []:
    ts = datetime.fromtimestamp(o.time_setup, tz=utc)
    print(f"  set {ts.strftime('%m-%d %H:%M:%S')} {TYPES.get(o.type, o.type):<9} "
          f"{o.volume_current:.2f} @ {o.price_open:.2f}  magic {o.magic}  {o.comment}")

deals = mt5.history_deals_get(datetime(2026, 8, 5, tzinfo=utc),
                              datetime(2026, 8, 7, tzinfo=utc))
print(f"\ndeals on/after Aug 5 (server): {0 if deals is None else len(deals)}")
for d in deals or []:
    ts = datetime.fromtimestamp(d.time, tz=utc)
    print(f"  {ts.strftime('%m-%d %H:%M:%S')} type{d.type} {d.volume:.2f} "
          f"@ {d.price:.2f} profit {d.profit:+.2f} {d.comment}")
mt5.shutdown()
