"""Summarize per-cycle results from bot.log STATS lines.

Compounds the full-size equivalent (pct-of-basis applied to FULL_START), and —
for cycles tagged with a v4 regime verdict — compares:
  v3 actual   = every tagged cycle traded
  v4 simulated = only the cycles the regime filter would have traded
"""
import re

FULL_START = 1278.08   # balance when fixed-lot test mode began (2026-07-30)

PAT = re.compile(r"STATS cycle=(\d+) outcome=(\w+) start=([\d.]+) end=([\d.]+) "
                 r"pnl=([+-][\d.]+)"
                 r"(?: step=([\d.]+) basis=([\d.]+) pct=([+-][\d.]+))?"
                 r"(?: regime=(\w+))?")

rows = []
with open("bot.log", encoding="utf-8") as f:
    for line in f:
        m = PAT.search(line)
        if m:
            rows.append((line[1:20], int(m[1]), m[2], float(m[3]), float(m[4]),
                         float(m[5]),
                         float(m[6]) if m[6] else None,
                         float(m[7]) if m[7] else None,
                         float(m[8]) if m[8] else None,
                         m[9]))

if not rows:
    print("No completed cycles logged yet.")
    raise SystemExit

full = FULL_START
print(f"{'time':<20}{'cyc':>4}  {'outcome':<11}{'step':>6}{'v4?':>6}{'pnl':>9}"
      f"{'pct':>8}{'balance':>10}{'full-size':>11}")
for ts, cyc, out, start, end, pnl, step, basis, pct, regime in rows:
    if pct is not None:
        full *= 1 + pct
    print(f"{ts:<20}{cyc:>4}  {out:<11}"
          f"{(f'{step:.2f}' if step else '0.30'):>6}"
          f"{(regime or '—'):>6}{pnl:>+9.2f}"
          f"{(f'{pct * 100:+.1f}%' if pct is not None else '—'):>8}"
          f"{end:>10.2f}{full:>11.2f}")


def summarize(label, subset):
    if not subset:
        print(f"{label}: no cycles")
        return
    wins = [r for r in subset if r[5] > 0]
    comp = 1.0
    for r in subset:
        comp *= 1 + r[8]
    print(f"{label}: {len(subset)} cycles | {len(wins)}W/{len(subset) - len(wins)}L "
          f"| net {sum(r[5] for r in subset):+.2f} USD "
          f"| compounded {comp * 100 - 100:+.1f}%")


scored = [r for r in rows if r[8] is not None]
wins = [r for r in scored if r[5] > 0]
print(f"\nTest-mode cycles: {len(scored)} | wins {len(wins)} / "
      f"losses {len(scored) - len(wins)}")
print(f"Full-size equivalent: {FULL_START:.2f} -> {full:.2f} "
      f"({100 * (full / FULL_START - 1):+.1f}%)")

tagged = [r for r in scored if r[9]]
if tagged:
    print("\n--- v3 vs v4 (tagged cycles only) ---")
    summarize("v3 actual (all)     ", tagged)
    summarize("v4 sim (trade-only) ", [r for r in tagged if r[9] == "trade"])
    summarize("  skipped by filter ", [r for r in tagged if r[9] == "skip"])
