"""Read Fusion Markets XAUUSD spread stats from recent M1 bars (works with
whatever account the default terminal is logged into — no credentials)."""
import MetaTrader5 as mt5

mt5.initialize()
a = mt5.account_info()
print(f"Account: {a.login} @ {a.server}")
mt5.symbol_select("XAUUSD", True)
r = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M1, 0, 120)
if r is None or len(r) == 0:
    print("no bars:", mt5.last_error())
else:
    i = mt5.symbol_info("XAUUSD")
    sp = [int(b["spread"]) for b in r]
    avg = sum(sp) / len(sp)
    print(f"point {i.point} | {len(r)} M1 bars (last = Friday close)")
    print(f"spread: min {min(sp)} / avg {avg:.1f} / max {max(sp)} points")
    print(f"      = min ${min(sp) * i.point:.2f} / avg ${avg * i.point:.3f} / max ${max(sp) * i.point:.2f}")
mt5.shutdown()
