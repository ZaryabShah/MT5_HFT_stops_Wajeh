"""Parameter sweep over 10 days of recorded ticks. Writes sweep_results.csv
and prints the top configs by net P/L with drawdown context."""
import csv
import itertools
import time

from backtest import DEFAULT, build_seconds, minute_ranges, run

GRID = dict(
    sl_pct=[0.05, 0.06, 0.08],
    trail_arm=[0.4, 0.5, 0.6],
    trail_giveback=[0.2, 0.3, 0.4],
    purge_at=[4, 5],
    step_cap=[0.60, 0.90, 1.20, None],
    regime_mult=[None, 4.0],
)

secs = build_seconds()
rng = minute_ranges(secs)

keys = list(GRID)
combos = list(itertools.product(*GRID.values()))
print(f"{len(combos)} configs x {len(secs['t']):,} seconds")

rows = []
t0 = time.time()
for idx, vals in enumerate(combos):
    cfg = dict(DEFAULT)
    cfg.update(dict(zip(keys, vals)))
    r = run(cfg, secs, rng)
    rows.append({**dict(zip(keys, vals)), "net": round(r["net"], 2),
                 "cycles": r["n"], "win_rate": round(r["win_rate"], 3),
                 "max_dd": round(r["max_dd"], 2)})
    if (idx + 1) % 25 == 0:
        el = time.time() - t0
        print(f"  {idx + 1}/{len(combos)} ({el:.0f}s, ~{el / (idx + 1) * (len(combos) - idx - 1):.0f}s left)")

rows.sort(key=lambda x: -x["net"])
with open("sweep_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

print("\n=== TOP 15 by net (10 days, 0.01 lots) ===")
hdr = f"{'net':>8} {'maxDD':>8} {'cyc':>4} {'win%':>5}  sl  arm  gvbk  purge  cap    gate"
print(hdr)
for r in rows[:15]:
    print(f"{r['net']:>8.2f} {r['max_dd']:>8.2f} {r['cycles']:>4} {r['win_rate']*100:>4.0f}%  "
          f"{r['sl_pct']:.2f} {r['trail_arm']:.1f}  {r['trail_giveback']:.1f}   "
          f"{r['purge_at']}     {str(r['step_cap']):<5} {r['regime_mult']}")

print("\n=== reference configs ===")
for r in rows:
    if (r["sl_pct"], r["trail_arm"], r["trail_giveback"], r["purge_at"]) == (0.08, 0.5, 0.3, 4):
        if r["step_cap"] == 0.90 and r["regime_mult"] is None:
            print(f"v4.1 live config:      net {r['net']:+.2f}, maxDD {r['max_dd']:.2f}, "
                  f"{r['cycles']} cycles, {r['win_rate']*100:.0f}% wins")
        if r["step_cap"] is None and r["regime_mult"] == 4.0:
            print(f"v4 (gate, no cap):     net {r['net']:+.2f}, maxDD {r['max_dd']:.2f}, "
                  f"{r['cycles']} cycles, {r['win_rate']*100:.0f}% wins")
        if r["step_cap"] is None and r["regime_mult"] is None:
            print(f"v3 (no cap, no gate):  net {r['net']:+.2f}, maxDD {r['max_dd']:.2f}, "
                  f"{r['cycles']} cycles, {r['win_rate']*100:.0f}% wins")
print("\nFull table: sweep_results.csv")
