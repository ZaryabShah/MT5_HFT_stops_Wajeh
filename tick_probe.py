"""Demo: fetch raw ticks from MT5 and aggregate to 1-second bars."""
from datetime import datetime, timezone

import MetaTrader5 as mt5

import config as C

mt5.initialize(login=C.MT5_LOGIN, password=C.MT5_PASSWORD, server=C.MT5_SERVER)
mt5.symbol_select(C.SYMBOL, True)

# Friday's last active hour (UTC guess; we inspect what comes back)
frm = datetime(2026, 7, 31, 15, 0, tzinfo=timezone.utc)
ticks = mt5.copy_ticks_from(C.SYMBOL, frm, 200_000, mt5.COPY_TICKS_ALL)
if ticks is None or len(ticks) == 0:
    print("no ticks:", mt5.last_error())
    mt5.shutdown()
    raise SystemExit

t0, t1 = ticks[0], ticks[-1]
print(f"Got {len(ticks):,} ticks")
print(f"First: {datetime.fromtimestamp(t0['time'], tz=timezone.utc)} bid {t0['bid']} ask {t0['ask']} (ms={t0['time_msc'] % 1000})")
print(f"Last:  {datetime.fromtimestamp(t1['time'], tz=timezone.utc)} bid {t1['bid']} ask {t1['ask']}")
span = t1["time"] - t0["time"]
print(f"Span: {span / 3600:.2f} hours -> {len(ticks) / max(span, 1):.1f} ticks/second average")

# aggregate to 1-second OHLC (bid)
bars = {}
for tk in ticks:
    sec = int(tk["time"])
    b = tk["bid"]
    if b == 0:
        continue
    if sec not in bars:
        bars[sec] = [b, b, b, b]          # o h l c
    else:
        r = bars[sec]
        r[1] = max(r[1], b)
        r[2] = min(r[2], b)
        r[3] = b
print(f"\nAggregated: {len(bars):,} one-second bars")
sample = sorted(bars)[len(bars) // 2]
o, h, l, c_ = bars[sample]
print(f"Sample 1s bar @ {datetime.fromtimestamp(sample, tz=timezone.utc)}: O {o} H {h} L {l} C {c_}")

mt5.shutdown()
