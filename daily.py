"""Day-by-day breakdown of the v4.2 config over the 10 backtest days:
fixed-lot (0.01) balance path AND the compounded full-size equivalent."""
from datetime import datetime, timezone

from backtest import DEFAULT, build_seconds, minute_ranges, run

START_BALANCE = 1310.54     # account balance going into Monday

cfg = dict(DEFAULT)
cfg.update(dict(sl_pct=0.06, trail_arm=0.5, trail_giveback=0.4,
                purge_at=5, step_cap=None, regime_mult=4.0))

secs = build_seconds()
rng = minute_ranges(secs)
res = run(cfg, secs, rng)

days = {}
for c in res["cycles"]:
    d = datetime.fromtimestamp(c["t"], tz=timezone.utc).strftime("%a %m-%d")
    days.setdefault(d, []).append(c)

bal = START_BALANCE
comp = START_BALANCE
print(f"v4.2 config, 10 days, starting balance {START_BALANCE:.2f}")
print(f"{'day':<10}{'cyc':>4}{'W-L':>7}{'day net$':>10}{'balance':>10}"
      f"{'day %':>8}{'compounded':>12}")
for d, cs in days.items():
    net = sum(c["pnl"] for c in cs)
    w = sum(1 for c in cs if c["pnl"] > 0)
    bal += net
    fac = 1.0
    for c in cs:
        fac *= 1 + c["pct"]
    comp *= fac
    print(f"{d:<10}{len(cs):>4}{f'{w}-{len(cs)-w}':>7}{net:>+10.2f}{bal:>10.2f}"
          f"{(fac-1)*100:>+7.1f}%{comp:>12.2f}")
print(f"\nfixed 0.01 lots: {START_BALANCE:.2f} -> {bal:.2f} "
      f"({(bal/START_BALANCE-1)*100:+.1f}%)")
print(f"compounded full-size equivalent: {START_BALANCE:.2f} -> {comp:.2f} "
      f"({(comp/START_BALANCE-1)*100:+.1f}%)")
