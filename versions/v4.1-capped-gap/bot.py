"""XAUUSD grid bot (Wajeh strategy) — Exness MT5 demo.

Strategy:
  1. Start, wait 60s.
  2. Anchor at current price. Place 11 BUY STOPS above (0.30 apart, first at +0.30)
     and 11 SELL STOPS below (0.30 apart, first at -0.30).
  3. Lot per level sized so a straight one-directional run to level 10
     earns 12% of cycle-start balance (floored at broker min lot).
  4. Monitor equity vs cycle-start balance:
       * profit >= 12%  -> close ALL positions + pending orders, wait 30s, new cycle.
       * ALL 22 stops triggered (both sides fully hit) -> close everything, bot exits.
  5. No orders are re-placed mid-cycle: once a side is consumed it stays consumed
     until target or full double-side fill ends the cycle.

Run:  python bot.py
Logs: bot.log
"""
import sys
import time
from datetime import datetime

import MetaTrader5 as mt5

import config as C

LOG_FILE = "bot.log"
POLL_SEC = 0.5          # equity check interval
DEVIATION = 100         # max slippage (points) on market close orders


# ----------------------------------------------------------------------------
def log(msg: str):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def connect() -> bool:
    for attempt in range(1, 6):
        if mt5.initialize(login=C.MT5_LOGIN, password=C.MT5_PASSWORD, server=C.MT5_SERVER):
            acc = mt5.account_info()
            log(f"Connected: login {acc.login} @ {acc.server} | balance {acc.balance} {acc.currency}")
            if not mt5.symbol_select(C.SYMBOL, True):
                log(f"FATAL: cannot select symbol {C.SYMBOL}: {mt5.last_error()}")
                return False
            return True
        log(f"initialize() failed (attempt {attempt}/5): {mt5.last_error()}")
        time.sleep(3)
    return False


def grid_step(spec) -> float:
    """Grid spacing for this cycle: fixed, or scaled to recent 1-min volatility."""
    if not C.ADAPTIVE_STEP:
        return C.GRID_STEP
    rates = mt5.copy_rates_from_pos(C.SYMBOL, mt5.TIMEFRAME_M1, 1, C.VOL_LOOKBACK_MIN)
    if rates is None or len(rates) == 0:
        return C.GRID_STEP
    avg_range = sum(float(r["high"] - r["low"]) for r in rates) / len(rates)
    return max(C.GRID_STEP, round(C.VOL_STEP_MULT * avg_range, spec.digits))


def calc_lot(balance: float, spec, step: float) -> float:
    """Lot per level so that a straight run to TARGET_LEVEL yields PROFIT_TARGET_PCT.

    Profit if price runs to level N without touching the other side:
        sum_{i=1}^{N-1} (P_N - P_i) * contract * lot
      = contract * lot * step * N*(N-1)/2
    """
    raw = raw_lot(balance, spec, step)
    vstep = spec.volume_step
    lot = round(raw / vstep) * vstep
    lot = max(spec.volume_min, min(lot, spec.volume_max))
    return round(lot, 8)


def raw_lot(balance: float, spec, step: float) -> float:
    n = C.TARGET_LEVEL
    per_lot = spec.trade_contract_size * step * n * (n - 1) / 2
    return balance * C.PROFIT_TARGET_PCT / per_lot


def send_with_retry(request: dict, what: str):
    for attempt in range(1, 4):
        result = mt5.order_send(request)
        if result is None:
            log(f"  {what}: order_send returned None: {mt5.last_error()} (attempt {attempt})")
        elif result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
        else:
            log(f"  {what}: retcode {result.retcode} ({result.comment}) (attempt {attempt})")
        time.sleep(0.3)
    return None


def place_stop(side: str, otype, price: float, lot: float, level: int) -> str:
    """Place one stop order. If the market has already crossed the level while we
    were placing (fast move -> 'bad stops'/'invalid price'), enter at market
    instead — that is exactly what the stop would have done. Returns
    'pending' | 'market' | 'failed'."""
    req = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": C.SYMBOL,
        "volume": lot,
        "type": otype,
        "price": price,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
        "magic": C.MAGIC,
        "comment": f"WajehGrid L{level}",
    }
    if send_with_retry(req, f"{side} L{level} @ {price}"):
        return "pending"
    tick = mt5.symbol_info_tick(C.SYMBOL)
    crossed = (otype == mt5.ORDER_TYPE_BUY_STOP and tick.ask >= price) or (
        otype == mt5.ORDER_TYPE_SELL_STOP and tick.bid <= price)
    if crossed:
        mreq = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": C.SYMBOL,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if otype == mt5.ORDER_TYPE_BUY_STOP else mt5.ORDER_TYPE_SELL,
            "price": tick.ask if otype == mt5.ORDER_TYPE_BUY_STOP else tick.bid,
            "deviation": DEVIATION,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "magic": C.MAGIC,
            "comment": f"WajehGrid L{level} mkt",
        }
        if send_with_retry(mreq, f"{side} L{level} -> MARKET"):
            log(f"  {side} L{level} @ {price}: level already crossed, entered at market.")
            return "market"
    log(f"  {side} L{level} @ {price}: FAILED — hole in grid.")
    return "failed"


def place_grid(spec, lot: float, step: float):
    """Place 11 buy stops above and 11 sell stops below current price."""
    tick = mt5.symbol_info_tick(C.SYMBOL)
    anchor_ask, anchor_bid = tick.ask, tick.bid
    digits = spec.digits
    pending = market = 0
    for i in range(1, C.GRID_LEVELS + 1):
        for side, otype, price in (
            ("BUY STOP", mt5.ORDER_TYPE_BUY_STOP, round(anchor_ask + i * step, digits)),
            ("SELL STOP", mt5.ORDER_TYPE_SELL_STOP, round(anchor_bid - i * step, digits)),
        ):
            outcome = place_stop(side, otype, price, lot, i)
            if outcome == "pending":
                pending += 1
            elif outcome == "market":
                market += 1
    log(f"Grid placed: {pending} pendings + {market} market fills "
        f"/ {C.GRID_LEVELS * 2} levels (anchor ask {anchor_ask} / bid {anchor_bid}, lot {lot})")
    return pending + market


def my_positions():
    """Our open positions, or None on terminal error (do NOT treat as flat)."""
    res = mt5.positions_get(symbol=C.SYMBOL)
    return None if res is None else [p for p in res if p.magic == C.MAGIC]


def my_orders():
    """Our pending orders, or None on terminal error (do NOT treat as flat)."""
    res = mt5.orders_get(symbol=C.SYMBOL)
    return None if res is None else [o for o in res if o.magic == C.MAGIC]


def close_all():
    """Cancel every pending order, then close every open position (ours only).
    Retries until flat (up to 10 rounds)."""
    for round_no in range(10):
        orders = my_orders()
        positions = my_positions()
        if orders is None or positions is None:   # terminal glitch — retry
            time.sleep(0.5)
            continue
        if not orders and not positions:
            log("All positions closed, all pendings cancelled — flat.")
            return True
        if round_no:
            log(f"close_all retry {round_no}: {len(positions)} positions, "
                f"{len(orders)} pendings remain")
        for o in orders:
            send_with_retry({"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket},
                            f"cancel #{o.ticket}")
        for p in positions:
            tick = mt5.symbol_info_tick(C.SYMBOL)
            is_buy = p.type == mt5.POSITION_TYPE_BUY
            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": C.SYMBOL,
                "volume": p.volume,
                "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
                "position": p.ticket,
                "price": tick.bid if is_buy else tick.ask,
                "deviation": DEVIATION,
                "type_filling": mt5.ORDER_FILLING_FOK,
                "magic": C.MAGIC,
                "comment": "WajehGrid close",
            }
            send_with_retry(req, f"close #{p.ticket}")
        time.sleep(0.5)
    log(f"WARNING: could not fully flatten: {len(my_positions())} positions remain.")
    return False


def purge_side(kind: str):
    """Close all positions and cancel all pending stops on one side."""
    ptype = mt5.POSITION_TYPE_BUY if kind == "buy" else mt5.POSITION_TYPE_SELL
    otype = mt5.ORDER_TYPE_BUY_STOP if kind == "buy" else mt5.ORDER_TYPE_SELL_STOP
    for o in my_orders() or []:
        if o.type == otype:
            send_with_retry({"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket},
                            f"purge cancel #{o.ticket}")
    for p in my_positions() or []:
        if p.type == ptype:
            tick = mt5.symbol_info_tick(C.SYMBOL)
            is_buy = ptype == mt5.POSITION_TYPE_BUY
            send_with_retry({
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": C.SYMBOL,
                "volume": p.volume,
                "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
                "position": p.ticket,
                "price": tick.bid if is_buy else tick.ask,
                "deviation": DEVIATION,
                "type_filling": mt5.ORDER_FILLING_FOK,
                "magic": C.MAGIC,
                "comment": "WajehGrid purge",
            }, f"purge close #{p.ticket}")


def run_cycle(cycle_no: int, spec) -> str:
    """Returns 'target' | 'all_filled' | 'empty' | 'error'."""
    acc = mt5.account_info()
    start_balance = acc.balance
    raw_step = grid_step(spec)      # uncapped volatility measure (regime gate metric)
    step = min(raw_step, C.GRID_STEP_MAX) if C.GRID_STEP_MAX else raw_step
    n = C.TARGET_LEVEL
    if C.FIXED_TEST_LOT:
        lot = C.FIXED_TEST_LOT
        # virtual balance for which this lot is the exact spec size
        basis = lot * spec.trade_contract_size * step * n * (n - 1) / 2 \
            / C.PROFIT_TARGET_PCT
    else:
        lot = calc_lot(start_balance, spec, step)
        raw = raw_lot(start_balance, spec, step)
        basis = start_balance
        if lot > raw * 1.5:
            needed = spec.volume_min * spec.trade_contract_size * step * n * (n - 1) / 2 \
                / C.PROFIT_TARGET_PCT
            log(f"WARNING: min-lot oversize x{lot / raw:.1f} — balance for exact "
                f"sizing at this step: {needed:.0f}")
    target_usd = basis * C.PROFIT_TARGET_PCT
    maxloss_usd = basis * C.MAX_CYCLE_LOSS_PCT
    straight_run_profit = spec.trade_contract_size * step * n * (n - 1) / 2 * lot
    tick0 = mt5.symbol_info_tick(C.SYMBOL)
    spread0 = (tick0.ask - tick0.bid) if tick0 else 0.0
    regime = "trade"
    if C.MIN_STEP_SPREAD_MULT and raw_step < spread0 * C.MIN_STEP_SPREAD_MULT:
        regime = "skip"
    log(f"===== CYCLE {cycle_no} ===== balance {start_balance:.2f}, basis {basis:.2f}, "
        f"target +{target_usd:.2f} (12%), stop -{maxloss_usd:.2f} (8%), "
        f"step {step:.2f} (raw {raw_step:.2f}), lot/level {lot}, v4-verdict {regime} "
        f"(straight run to L{n} would earn {straight_run_profit:.2f})")

    placed = place_grid(spec, lot, step)
    if placed == 0:
        log("ERROR: no orders placed, aborting cycle.")
        return "error"

    peak = 0.0
    purged = False
    while True:
        time.sleep(POLL_SEC)
        acc = mt5.account_info()
        if acc is None:                      # terminal hiccup — try to reconnect
            log("account_info() None, reconnecting...")
            if not connect():
                return "error"
            continue
        profit = acc.equity - start_balance
        pendings = my_orders()
        positions = my_positions()
        if pendings is None or positions is None:
            continue                    # terminal glitch — never act on unknown state

        def end_cycle(outcome: str) -> str:
            close_all()
            a = mt5.account_info()
            pnl = a.balance - start_balance
            log(f"Cycle {cycle_no} done ({outcome}). New balance: {a.balance:.2f}")
            log(f"STATS cycle={cycle_no} outcome={outcome} start={start_balance:.2f} "
                f"end={a.balance:.2f} pnl={pnl:+.2f} step={step:.2f} "
                f"basis={basis:.2f} pct={pnl / basis:+.4f} regime={regime}")
            return outcome

        peak = max(peak, profit)

        if profit >= target_usd:
            log(f"TARGET HIT: +{profit:.2f} (>= {target_usd:.2f}). Closing everything.")
            return end_cycle("target")

        if (C.TRAIL_ARM_FRAC and peak >= target_usd * C.TRAIL_ARM_FRAC
                and profit <= peak - target_usd * C.TRAIL_GIVEBACK_FRAC):
            log(f"TRAIL EXIT: peak was +{peak:.2f}, now +{profit:.2f}. Banking.")
            return end_cycle("trail")

        if C.PURGE_OPPOSITE_AT and not purged:
            longs_n = sum(1 for p in positions if p.type == mt5.POSITION_TYPE_BUY)
            shorts_n = len(positions) - longs_n
            side = None
            if longs_n >= C.PURGE_OPPOSITE_AT and shorts_n <= 2:
                side = "sell"
            elif shorts_n >= C.PURGE_OPPOSITE_AT and longs_n <= 2:
                side = "buy"
            if side:
                log(f"TREND PURGE: {longs_n} longs / {shorts_n} shorts — "
                    f"dropping the {side} side (P/L {profit:+.2f}).")
                purge_side(side)
                purged = True

        if C.MAX_CYCLE_LOSS_PCT and profit <= -maxloss_usd:
            log(f"EQUITY STOP: {profit:+.2f} (<= -{maxloss_usd:.2f}). "
                f"Flattening & re-anchoring.")
            return end_cycle("equitystop")

        if C.MAX_LOCKED_PAIRS:
            longs = sum(1 for p in positions if p.type == mt5.POSITION_TYPE_BUY)
            locked = min(longs, len(positions) - longs)
            if locked >= C.MAX_LOCKED_PAIRS:
                log(f"PAIR CAP: {locked} locked buy/sell pairs (>= {C.MAX_LOCKED_PAIRS}), "
                    f"P/L {profit:+.2f}. Flattening & re-anchoring.")
                return end_cycle("paircap")

        if not pendings:
            if positions:
                # every one of the 22 stops has been consumed -> full double fill
                log(f"ALL {placed} STOPS TRIGGERED (both sides fully hit). "
                    f"P/L now {profit:.2f}. Closing everything.")
                return end_cycle("all_filled")
            if acc.balance < 1.0:
                log(f"STOP OUT: broker force-closed everything, balance {acc.balance:.2f}. "
                    f"Cycle P/L {acc.balance - start_balance:+.2f}.")
                return "stopout"
            log("No pendings and no positions left (closed externally?). Ending cycle.")
            return "empty"


def main():
    log("Bot starting.")
    if not connect():
        log("FATAL: could not connect to MT5.")
        sys.exit(1)

    spec = mt5.symbol_info(C.SYMBOL)
    log(f"{C.SYMBOL}: contract {spec.trade_contract_size}, digits {spec.digits}, "
        f"min lot {spec.volume_min}, spread now "
        f"{round((mt5.symbol_info_tick(C.SYMBOL).ask - mt5.symbol_info_tick(C.SYMBOL).bid), spec.digits)}")

    # Never stack a new grid on leftovers from a previous run
    if my_orders() or my_positions():
        log(f"Startup cleanup: {len(my_positions())} positions / "
            f"{len(my_orders())} pendings from a previous run — flattening.")
        close_all()

    log(f"Waiting {C.START_DELAY_SEC}s before first grid (per spec)...")
    time.sleep(C.START_DELAY_SEC)

    cycle_no = 0
    try:
        while True:
            acc = mt5.account_info()
            if acc and acc.balance < 1.0:
                log(f"Balance {acc.balance:.2f} — too low to trade. "
                    f"Top up the demo account, then restart the bot.")
                break
            if C.MIN_STEP_SPREAD_MULT and not C.REGIME_SHADOW_MODE:
                waiting = False
                while True:
                    tick = mt5.symbol_info_tick(C.SYMBOL)
                    step_now = grid_step(spec)
                    if tick and step_now >= (tick.ask - tick.bid) * C.MIN_STEP_SPREAD_MULT:
                        break
                    if not waiting:
                        log(f"REGIME WAIT: step {step_now:.2f} < "
                            f"{C.MIN_STEP_SPREAD_MULT:.0f}x spread "
                            f"{tick.ask - tick.bid:.2f} — market too quiet, sitting out "
                            f"(rechecking every {C.REGIME_WAIT_SEC}s).")
                        waiting = True
                    time.sleep(C.REGIME_WAIT_SEC)
                if waiting:
                    log(f"REGIME OK: step {step_now:.2f} clears the spread filter. Resuming.")

            cycle_no += 1
            outcome = run_cycle(cycle_no, spec)
            if outcome in ("target", "trail", "paircap", "equitystop", "all_filled"):
                log(f"Waiting {C.RESTART_DELAY_SEC}s, then re-anchoring...")
                time.sleep(C.RESTART_DELAY_SEC)
                continue
            if outcome == "stopout":
                log("Account stopped out — bot stops. Top up the demo, then restart.")
                break
            if outcome == "empty":
                log("Nothing left to manage — stopping.")
                break
            if outcome == "error":
                log("Stopping on error.")
                break
    except KeyboardInterrupt:
        log("Interrupted by user. NOTE: existing orders/positions were left untouched. "
            "Run 'python close_all.py' to flatten.")
    finally:
        mt5.shutdown()
        log("Bot stopped.")


if __name__ == "__main__":
    main()
