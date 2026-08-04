"""READ-ONLY audit of the Fusion demo: every deal since Aug 3, with per-day
and per-window sums, to reconcile the user's live 0.02-lot run vs the replay."""
from collections import defaultdict
from datetime import datetime, timezone

import MetaTrader5 as mt5

assert mt5.initialize(login=426190, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
acc = mt5.account_info()
print(f"connected: {acc.login} @ {acc.server} | balance {acc.balance:.2f} "
      f"| equity {acc.equity:.2f}")

utc = timezone.utc
deals = mt5.history_deals_get(datetime(2026, 8, 3, tzinfo=utc),
                              datetime(2026, 8, 7, tzinfo=utc))
print(f"deals since Aug 3: {0 if deals is None else len(deals)}")

TYPES = {0: "buy", 1: "sell", 2: "bal"}
days = defaultdict(float)
if deals:
    print(f"\n{'time(server)':<17}{'type':<5}{'vol':>5}{'price':>9}"
          f"{'profit':>9}{'comm':>7}{'swap':>6}{'magic':>8} comment")
    for d in deals:
        ts = datetime.fromtimestamp(d.time, tz=utc)
        net = d.profit + d.commission + d.swap
        days[ts.strftime("%a %m-%d")] += net
        print(f"{ts.strftime('%m-%d %H:%M:%S'):<17}{TYPES.get(d.type, d.type):<5}"
              f"{d.volume:>5.2f}{d.price:>9.2f}{d.profit:>9.2f}"
              f"{d.commission:>7.2f}{d.swap:>6.2f}{d.magic:>8} {d.comment}")
    print("\nper server-day net (profit+comm+swap):")
    for k, v in days.items():
        print(f"  {k}: {v:+.2f}")

orders = mt5.orders_get()
poss = mt5.positions_get()
print(f"\nopen now: {0 if poss is None else len(poss)} positions, "
      f"{0 if orders is None else len(orders)} pendings")
mt5.shutdown()
