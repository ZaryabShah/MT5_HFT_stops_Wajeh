"""Read-only probe: connect to MT5, verify login, dump account + XAUUSD specs,
and show the computed lot sizing. Places NO orders."""
import MetaTrader5 as mt5
import config as C


def main():
    if not mt5.initialize(login=C.MT5_LOGIN, password=C.MT5_PASSWORD, server=C.MT5_SERVER):
        print("initialize() failed:", mt5.last_error())
        return

    acc = mt5.account_info()
    print(f"Connected: {acc.name} | login {acc.login} | server {acc.server}")
    print(f"Balance: {acc.balance} {acc.currency} | Equity: {acc.equity} | Leverage: 1:{acc.leverage}")
    print(f"Trade allowed: {acc.trade_allowed} | Margin mode: {acc.margin_mode} (2 = hedging)")

    if not mt5.symbol_select(C.SYMBOL, True):
        print(f"symbol_select({C.SYMBOL}) failed:", mt5.last_error())
        mt5.shutdown()
        return

    s = mt5.symbol_info(C.SYMBOL)
    tick = mt5.symbol_info_tick(C.SYMBOL)
    print(f"\n--- {C.SYMBOL} ---")
    print(f"Bid/Ask: {tick.bid} / {tick.ask}  (spread {round((tick.ask - tick.bid) / s.point)} points)")
    print(f"Digits: {s.digits} | Point: {s.point}")
    print(f"Contract size: {s.trade_contract_size}")
    print(f"Tick value: {s.trade_tick_value} | Tick size: {s.trade_tick_size}")
    print(f"Volume min/step/max: {s.volume_min} / {s.volume_step} / {s.volume_max}")
    print(f"Stops level (min distance, points): {s.trade_stops_level}")
    print(f"Freeze level (points): {s.trade_freeze_level}")
    print(f"Filling modes bitmask: {s.filling_mode} | Trade mode: {s.trade_mode}")
    print(f"Margin per 1.0 lot (approx): {mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, C.SYMBOL, 1.0, tick.ask)}")

    # --- Lot sizing math ---
    # Buy stops at start+0.30*i (i=1..11). If price runs straight up and touches
    # level N, open profit = sum_{i=1}^{N-1} (P_N - P_i) * contract * lots
    #                      = contract * lots * step * sum_{k=1}^{N-1} k... wait, distances:
    # P_N - P_i = step*(N-i)  -> sum_{i=1}^{N-1} step*(N-i) = step * (N-1)N/2
    N = C.TARGET_LEVEL
    dollars_per_lot_at_target = s.trade_contract_size * C.GRID_STEP * (N - 1) * N / 2
    target_usd = acc.balance * C.PROFIT_TARGET_PCT
    raw_lot = target_usd / dollars_per_lot_at_target
    lot = max(s.volume_min, round(raw_lot / s.volume_step) * s.volume_step)
    print(f"\n--- Sizing ---")
    print(f"Target: {C.PROFIT_TARGET_PCT:.0%} of {acc.balance} = ${target_usd:.2f}")
    print(f"Profit per lot if price runs straight to level {N}: ${dollars_per_lot_at_target:.2f}")
    print(f"Raw lot per level: {raw_lot:.4f} -> rounded to step: {lot}")
    print(f"Margin for all 11 levels one side @ {lot} lots: "
          f"{mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, C.SYMBOL, lot * C.GRID_LEVELS, tick.ask):.2f}")

    # Worst case: all 22 orders triggered, full hedge. Max locked loss if both
    # sides fully filled: each buy/sell pair locks the distance between them.
    mt5.shutdown()


if __name__ == "__main__":
    main()
