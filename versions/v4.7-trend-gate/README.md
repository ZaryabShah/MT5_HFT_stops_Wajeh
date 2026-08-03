# v4.7 — v4.6 + trend classifier gate — LAUNCH CONFIG

Wajeh's idea ("classify trends and movements first, only trade when true"),
implemented as the measured 15-30min momentum edge from characterize.py.

## The gate
At cycle start, over the last 30 closed M1 bars, require BOTH:
- **Efficiency ratio** |net move| / sum|per-minute moves| **>= 0.25**
  (how much of the movement was travel vs noise)
- **|net move| >= $3.00** (the move is real, not micro-drift)
Fails -> wait, recheck every 2 min. Layered on top of all v4.6 rules.

## Evidence (real Fusion feed, 4 months, 0.01 lots)
| | v4.6 | **v4.7** |
|---|---|---|
| Net | +$1,857 | **+$3,165** |
| Max drawdown | −$808 | **−$404** |
| Net per $ of DD | 2.3 | **7.8** |
| Cycles | 617 | 572 |

Sweep showed a coherent plateau (mild 15/30-min gates all improve; strict or
60-min gates degrade) — pattern matches the pre-registered tape measurement,
not lottery selection. ER and move gates each passed 5-start robustness
(4/5 byte-identical).

## Full v4.7 stack
Fusion demo 426190 / XAUUSD / 0.01 lots · window 22-06 UTC · trend gate
(ER>=0.25 AND move>=$3 over 30m) · adaptive step (floor 0.30, cap 2.50) ·
regime gate step>=6x spread · 11+11 resting stops · purge 5-vs-<=2 · trail
0.5/0.3 · SL 8% of basis · pair cap 3 · 12% at last stop · daily breaker
-$50 · startup cleanup · magic 277888. Balance >= $1,000 comfortable
(maxDD -$404).

## Caveats
Now three stacked dimensions were selected on the same 4 months (params,
session, trend gate) — live results WILL be humbler than +$185/week. The
demo run is the out-of-sample judge.
