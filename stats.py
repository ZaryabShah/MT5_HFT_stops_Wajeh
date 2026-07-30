"""Summarize per-cycle results from bot.log STATS lines.

Also compounds what a FULLY-SIZED account would have done: each cycle's
pct-of-basis return applied to a virtual account starting at FULL_START.
"""
import re

FULL_START = 1278.08   # balance when fixed-lot test mode began (2026-07-30)

PAT = re.compile(r"STATS cycle=(\d+) outcome=(\w+) start=([\d.]+) end=([\d.]+) "
                 r"pnl=([+-][\d.]+)"
                 r"(?: step=([\d.]+) basis=([\d.]+) pct=([+-][\d.]+))?")

rows = []
with open("bot.log", encoding="utf-8") as f:
    for line in f:
        m = PAT.search(line)
        if m:
            ts = line[1:20]
            rows.append((ts, int(m[1]), m[2], float(m[3]), float(m[4]), float(m[5]),
                         float(m[6]) if m[6] else None,
                         float(m[7]) if m[7] else None,
                         float(m[8]) if m[8] else None))

if not rows:
    print("No completed cycles logged yet.")
    raise SystemExit

full = FULL_START
print(f"{'time':<20}{'cyc':>4}  {'outcome':<11}{'step':>6}{'pnl':>9}{'pct':>8}"
      f"{'balance':>10}{'full-size':>11}")
for ts, cyc, out, start, end, pnl, step, basis, pct in rows:
    if pct is not None:
        full *= 1 + pct
    print(f"{ts:<20}{cyc:>4}  {out:<11}"
          f"{step if step else 0.30:>6.2f}{pnl:>+9.2f}"
          f"{(f'{pct * 100:+.1f}%' if pct is not None else '—'):>8}"
          f"{end:>10.2f}{full:>11.2f}")

scored = [r for r in rows if r[8] is not None]
wins = [r for r in scored if r[5] > 0]
losses = [r for r in scored if r[5] <= 0]
print(f"\nTest-mode cycles: {len(scored)} | wins {len(wins)} / losses {len(losses)}"
      + (f" ({100 * len(wins) / len(scored):.0f}% win rate)" if scored else ""))
if wins:
    print(f"Avg win:  {100 * sum(r[8] for r in wins) / len(wins):+.1f}% of basis")
if losses:
    print(f"Avg loss: {100 * sum(r[8] for r in losses) / len(losses):+.1f}% of basis")
if scored:
    print(f"Full-size equivalent: {FULL_START:.2f} -> {full:.2f} "
          f"({100 * (full / FULL_START - 1):+.1f}%)")
