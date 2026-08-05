"""Fetch Aug 4-6 ticks from Fusion, replay server 01-06 of Aug 5 through the
v4.8 engine, and reconcile against the live deals on the account."""
from datetime import datetime, timezone

import MetaTrader5 as mt5
import numpy as np

from backtest import DEFAULT, build_seconds, minute_ranges, run

utc = timezone.utc
assert mt5.initialize(login=426190, password="Kazmi@12345",
                      server="FusionMarkets-Demo"), mt5.last_error()
tick = mt5.symbol_info_tick("XAUUSD")
print(f"server clock now: {datetime.fromtimestamp(tick.time, tz=utc)}")

ticks = mt5.copy_ticks_range("XAUUSD", datetime(2026, 8, 4, tzinfo=utc),
                             datetime(2026, 8, 6, tzinfo=utc), mt5.COPY_TICKS_ALL)
print(f"ticks fetched: {len(ticks):,}")
np.savez_compressed("data/ticks_aug5.npz", ticks=np.array(ticks))

deals = mt5.history_deals_get(datetime(2026, 8, 5, tzinfo=utc),
                              datetime(2026, 8, 6, tzinfo=utc))
poss = mt5.positions_get() or []
floating = sum(p.profit for p in poss)
acc = mt5.account_info()
mt5.shutdown()

secs = build_seconds("data/ticks_aug5.npz", "data/secs_aug5.npz")
rng = minute_ranges(secs)
t = secs["t"].astype(np.int64)
mid = (secs["bid_c"] + secs["ask_c"]) / 2
mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
bounds = np.append(idx, len(t))
m_close = mid[bounds[1:] - 1]
pref = np.cumsum(np.abs(np.diff(m_close, prepend=m_close[0])))
pos = np.searchsorted(uniq, mins) - 1
lo = pos - 30
net = np.abs(m_close[np.clip(pos, 0, None)] - m_close[np.clip(lo, 0, None)])
tot = pref[np.clip(pos, 0, None)] - pref[np.clip(lo, 0, None)]
er = np.where(tot > 1e-9, net / np.maximum(tot, 1e-9), 0.0)
GATE = (lo >= 0) & (er >= 0.25) & (net >= 3.0)

CFG = dict(DEFAULT)
CFG.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={0, 1, 2, 3, 4, 5}, gate_series=GATE))
t_aug5 = int(datetime(2026, 8, 5, tzinfo=utc).timestamp())
r = run(CFG, secs, rng, t_from=t_aug5)
print(f"\n=== REPLAY: Aug 5 server 01-06, v4.8 stack, 0.01 lots ===")
print(f"net {r['net']:+.2f} (x2 for 0.02 lots: {r['net'] * 2:+.2f}) | "
      f"{r['n']} cycles")
for c in r["cycles"]:
    d = datetime.fromtimestamp(int(c["t"]), tz=utc)
    print(f"   end {d.strftime('%H:%M:%S')}  {c['outcome']:<11} "
          f"step {c['step']:.2f}  {c['pnl']:>+7.2f}  (x2: {c['pnl'] * 2:+.2f})")

print(f"\n=== LIVE (deal history, Aug 5 server day) ===")
realized = sum(d.profit + d.commission + d.swap for d in deals or [])
closes = [d for d in (deals or []) if abs(d.profit) > 1e-9]
print(f"deals: {len(deals or [])} | realized {realized:+.2f} @0.02 "
      f"(= {realized / 2:+.2f} per 0.01)")
print(f"open now: {len(poss)} positions, floating {floating:+.2f} | "
      f"balance {acc.balance:.2f} | equity {acc.equity:.2f}")
if closes:
    print("closing deals:")
    for d in closes:
        ts = datetime.fromtimestamp(d.time, tz=utc)
        print(f"   {ts.strftime('%H:%M:%S')} profit {d.profit:+7.2f}  {d.comment}")
