"""Compounding study on the v4.7 cycle sequence (real Fusion feed, 4 months).

Models, all replayed over the SAME cycle sequence as the fixed-lot run:
  T1000: tiered rule — lot = floor(balance/$1000) x 0.01 (min 0.01), lot
         re-set at each UTC day start. Exact (P/L linear in lot; the $50/0.01
         breaker scales with lot, so the same days trip).
  SPEC : full spec compounding — every cycle sized so 12% target = 12% of
         CURRENT balance (continuous, no lot rounding): balance *= 1 + pct.
         APPROXIMATION: the day-breaker was applied at fixed-lot scale.
  SPECR: spec compounding with broker lot rounding (0.01 steps, min 0.01).
"""
from datetime import datetime, timedelta, timezone

from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)

V47 = dict(DEFAULT)
V47.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={22, 23, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))

res = run(V47, secs, rng)
cyc = res["cycles"]
print(f"reference fixed 0.01 lots: net {res['net']:+.2f} | "
      f"maxDD {res['max_dd']:+.2f} | {res['n']} cycles\n", flush=True)


def week_of(ts):
    d = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    return (d - timedelta(days=d.weekday())).strftime("%m-%d")


def weekly_table(title, path):
    """path: list of (t, balance_after, lot_used)."""
    print(f"--- {title} ---")
    print(f"{'week':<7}{'cyc':>4}{'lot rng':>12}{'start':>11}{'end':>11}"
          f"{'lowest':>11}{'net':>11}")
    prev_end = path[0][3]
    wkkey, rows = None, []
    agg = []
    for t, bal, lot, start_bal in path:
        k = week_of(t)
        if k != wkkey:
            if rows:
                agg.append((wkkey, rows))
            wkkey, rows = k, []
        rows.append((t, bal, lot, start_bal))
    if rows:
        agg.append((wkkey, rows))
    for k, rows in agg:
        start = rows[0][3]
        end = rows[-1][1]
        lo = min(r[1] for r in rows)
        lots = sorted({r[2] for r in rows})
        lotr = f"{lots[0]:.2f}" if len(lots) == 1 else f"{lots[0]:.2f}-{lots[-1]:.2f}"
        print(f"{k:<7}{len(rows):>4}{lotr:>12}{start:>11.2f}{end:>11.2f}"
              f"{lo:>11.2f}{end - start:>+11.2f}")
    print(flush=True)


def maxdd(path):
    peak, dd = -1e18, 0.0
    for _, bal, _, _ in path:
        peak = max(peak, bal)
        dd = min(dd, bal - peak)
    return dd


def maxdd_pct(path):
    peak, dd = 1e-9, 0.0
    for _, bal, _, _ in path:
        peak = max(peak, bal)
        dd = min(dd, bal / peak - 1)
    return dd


# ---- T1000: tiered daily ----
for start0 in (1000.0, 2000.0):
    bal, lot, cur_day = start0, 0.01, None
    path = []
    for c in cyc:
        day = c["t"] // 86400
        if day != cur_day:
            cur_day = day
            lot = max(0.01, int(bal // 1000) * 0.01)
        sb = bal
        bal += c["pnl"] * lot / 0.01
        path.append((c["t"], bal, lot, sb))
    print(f"T1000 from ${start0:.0f}: final {bal:.2f} "
          f"(net {bal - start0:+.2f}) | maxDD {maxdd(path):+.2f} | "
          f"min bal {min(p[1] for p in path):.2f} | end lot "
          f"{path[-1][2]:.2f}")
    if start0 == 1000.0:
        weekly_table("T1000 tiered compounding from $1,000 (weekly)", path)

# ---- SPEC: continuous ----
bal = 1000.0
path = []
for c in cyc:
    sb = bal
    bal *= 1 + c["pct"]
    path.append((c["t"], bal, bal * 0.01 / max(c["basis"], 1e-9), sb))
print(f"SPEC continuous from $1,000: final {bal:,.2f} "
      f"(x{bal / 1000:,.1f}) | maxDD% {maxdd_pct(path) * 100:.1f}% | "
      f"min bal {min(p[1] for p in path):,.2f}")
weekly_table("SPEC full compounding from $1,000 (weekly)", path)

# ---- SPECR: spec with lot rounding ----
for start0 in (1000.0, 200.0):
    bal = start0
    path = []
    dead = False
    for c in cyc:
        sb = bal
        lot = max(0.01, round(0.01 * bal / c["basis"], 2))
        bal += c["pnl"] * lot / 0.01
        path.append((c["t"], bal, lot, sb))
        if bal <= 50:
            dead = True
            break
    tag = "DEAD" if dead else "alive"
    print(f"SPECR (lot-rounded) from ${start0:.0f}: final {bal:,.2f} "
          f"[{tag}] | maxDD% {maxdd_pct(path) * 100:.1f}% | "
          f"min bal {min(p[1] for p in path):,.2f} | max lot "
          f"{max(p[2] for p in path):.2f}")
print("\nDONE research_compound", flush=True)
