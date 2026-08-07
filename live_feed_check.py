"""READ-ONLY live-vs-demo feed comparison (FusionMarkets-Live 487753 vs
Demo 429466). Specs, current quotes, H1 history overlap, tick spreads for
the same window. ENDS by re-logging the terminal into the DEMO account so
the running bot's session is restored."""
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
import numpy as np

utc = timezone.utc

# ---------- LIVE ----------
assert mt5.initialize(login=487753, password="Wajeh.277888",
                      server="FusionMarkets-Live"), mt5.last_error()
acc = mt5.account_info()
print(f"LIVE: {acc.login} @ {acc.server} | balance {acc.balance:.2f} "
      f"{acc.currency} | leverage 1:{acc.leverage}")
mt5.symbol_select("XAUUSD", True)
import time
time.sleep(2)
si = mt5.symbol_info("XAUUSD")
tick_live = mt5.symbol_info_tick("XAUUSD")
print(f"LIVE XAUUSD: contract {si.trade_contract_size}, digits {si.digits}, "
      f"min lot {si.volume_min}, swap L/S {si.swap_long}/{si.swap_short}, "
      f"stops_level {si.trade_stops_level}")
now = datetime.fromtimestamp(tick_live.time, tz=utc)
print(f"LIVE tick now: bid {tick_live.bid} ask {tick_live.ask} "
      f"(spread {tick_live.ask - tick_live.bid:.2f}) @ {now} server")

h1_live = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_H1,
                               now - timedelta(days=30), now)
t_from = now - timedelta(hours=3)
ticks_live = mt5.copy_ticks_range("XAUUSD", t_from, now, mt5.COPY_TICKS_ALL)
mt5.shutdown()

# ---------- DEMO (this also restores the bot's terminal login) ----------
assert mt5.initialize(login=429466, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
mt5.symbol_select("XAUUSD", True)
time.sleep(2)
tick_demo = mt5.symbol_info_tick("XAUUSD")
sid = mt5.symbol_info("XAUUSD")
print(f"\nDEMO tick now: bid {tick_demo.bid} ask {tick_demo.ask} "
      f"(spread {tick_demo.ask - tick_demo.bid:.2f})")
print(f"DEMO swap L/S {sid.swap_long}/{sid.swap_short}")
h1_demo = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_H1,
                               now - timedelta(days=30), now)
ticks_demo = mt5.copy_ticks_range("XAUUSD", t_from, now, mt5.COPY_TICKS_ALL)
acc2 = mt5.account_info()
print(f"terminal RESTORED to: {acc2.login} @ {acc2.server}")
mt5.shutdown()

# ---------- compare ----------
print("\n=== comparison ===")
print(f"price now: live mid {(tick_live.bid + tick_live.ask) / 2:.2f} vs "
      f"demo mid {(tick_demo.bid + tick_demo.ask) / 2:.2f} | diff "
      f"{abs((tick_live.bid + tick_live.ask) - (tick_demo.bid + tick_demo.ask)) / 2:.3f}")
if h1_live is not None and h1_demo is not None:
    L = {int(r["time"]): float(r["close"]) for r in h1_live}
    D = {int(r["time"]): float(r["close"]) for r in h1_demo}
    common = sorted(set(L) & set(D))
    diffs = np.array([abs(L[k] - D[k]) for k in common])
    print(f"H1 closes, last 30 days: {len(common)} shared bars | "
          f"mean |diff| {diffs.mean():.4f} | max |diff| {diffs.max():.3f}")
for name, tk in (("live", ticks_live), ("demo", ticks_demo)):
    if tk is not None and len(tk):
        a = np.array(tk)
        spr = a["ask"] - a["bid"]
        spr = spr[(a["bid"] > 0) & (a["ask"] > 0)]
        print(f"{name} ticks last 3h: {len(a):,} | avg spread {spr.mean():.4f} "
              f"| median {np.median(spr):.4f} | p95 {np.percentile(spr, 95):.4f}")
print("\nDONE live_feed_check")
