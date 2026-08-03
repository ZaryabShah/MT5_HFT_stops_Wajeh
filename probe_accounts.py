"""READ-ONLY probe of all three accounts: specs, leverage, gold spread stats
from M1 bar history. NO ORDERS ARE PLACED ANYWHERE IN THIS SCRIPT."""
import MetaTrader5 as mt5

ACCOUNTS = [
    ("Exness Standard demo", 472305567, "Wajeh.277888", "Exness-MT5Trial16"),
    ("Fusion ECN demo", 426190, "Kazmi@12345", "FusionMarkets-Demo"),
    ("Exness RAW **REAL**", 256723674, "Wajeh.277888", "Exness-MT5Real35"),
]

for name, login, pw, server in ACCOUNTS:
    print(f"\n===== {name} ({server}) =====")
    if not mt5.initialize(login=login, password=pw, server=server):
        print("  login failed:", mt5.last_error())
        mt5.shutdown()
        continue
    a = mt5.account_info()
    print(f"  login {a.login} | balance {a.balance} {a.currency} | "
          f"leverage 1:{a.leverage} | margin mode {a.margin_mode}")
    syms = [s.name for s in (mt5.symbols_get("*XAU*") or []) if "USD" in s.name]
    print(f"  gold symbols: {syms}")
    for sym in syms[:1]:
        mt5.symbol_select(sym, True)
        i = mt5.symbol_info(sym)
        r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 240)
        print(f"  {sym}: digits {i.digits}, contract {i.trade_contract_size}, "
              f"vol {i.volume_min}-{i.volume_max} step {i.volume_step}, "
              f"stops_level {i.trade_stops_level}")
        if r is not None and len(r):
            sp = [int(b["spread"]) for b in r]
            avg = sum(sp) / len(sp)
            print(f"  spread last {len(r)} M1 bars: min ${min(sp)*i.point:.3f} / "
                  f"avg ${avg*i.point:.3f} / max ${max(sp)*i.point:.3f}")
        else:
            print("  no bar history:", mt5.last_error())
    mt5.shutdown()
