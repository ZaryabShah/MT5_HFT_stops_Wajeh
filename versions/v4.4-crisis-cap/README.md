# v4.4 — v4.3 + $2.50 crisis cap — FINAL Monday config

One change vs v4.3: **`GRID_STEP_MAX = 2.50`** — the adaptive step may never
exceed $2.50. Normal markets are untouched (steps 0.3–1.8); only crisis hours
(April-style, raw steps $3–8) get trimmed, bounding one equity stop at
~$69 instead of $140–220.

Credit: Wajeh's hypothesis ("unlimited max space makes spaces very big
sometimes and cuts profits") — confirmed at the loose end of the range after
being falsified at the tight end ($0.90). Both results were real: tight caps
force noise-trading, loose caps bound tail risk.

## Evidence (4 months, Fusion costs, 0.01 lots, $50 daily breaker on)
| | v4.3 (no cap) | **v4.4 (cap 2.50)** |
|---|---|---|
| Net | +$1,861 | **+$2,291** |
| Max drawdown | −$1,251 | **−$984** |
| April net | −$550 | **+$48** |
| Lowest balance from $1,000 | −$79 (briefly negative!) | **$435** |
| Final balance | $2,861 | **$3,291** |
| Start-time robustness | 5/5 | **5/5, maxDD identical every run** |

## Full stack (deployment: Fusion demo, 0.01 lots, balance >= $1,500)
Adaptive step (0.5x avg 5-min range, floor $0.30, **cap $2.50**) · regime gate
(step >= 4x spread, recheck 120s) · 11+11 stops · purge at 5-vs-<=2 · trail
arm 50% / giveback 40% of target · equity stop -6% of basis · pair cap 3 ·
12% target at last stop · close on last-stop hit · 30s re-anchor ·
**daily breaker -$50 -> flat until next UTC day** · startup cleanup · magic 277888.
