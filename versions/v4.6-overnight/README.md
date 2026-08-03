# v4.6 — v4.5 + overnight-only window — LAUNCH CONFIG

One change vs v4.5: **`TRADE_HOURS = 22:00-06:00 UTC`** — new cycles start
only in this window (open cycles finish naturally). Credit: Wajeh proposed
session-testing ("22 to 4 UTC... test multiple").

## Why (real-feed session study, 4 months)
| Window | Net | maxDD | Win% |
|---|---|---|---|
| London 07-15 | −$1,208 | −$1,357 | 47% |
| US 12-20 | −$492 | −$1,199 | 47% |
| All hours (v4.5) | +$1,507 | −$1,195 | 49% |
| **22-06 (v4.6)** | **+$1,857** | **−$808** | **52%** |

Western-session volatility is whipsaw; overnight volatility trends cleanly.
Blocking London+US improves EVERY metric. Spread-by-hour is flat (~$0.08)
except 23 UTC rollover ($0.118) — spread filters tested and rejected.

## Evidence
- Real Fusion feed, 4 months: **+$1,857, maxDD −$808, 617 cycles, 52% wins**
- Robustness: 4/5 start times BYTE-IDENTICAL, 5th within 2.5%
- Weekly: $1,000 → $2,857, lowest ever $666, worst week −$401
- In-sample caveat: session choice selected on the same 4 months; the demo
  run is the out-of-sample test (~$110/week expectation)

## Full stack
Fusion demo 426190 / XAUUSD / 0.01 lots · adaptive step (0.5x 5-min range,
floor 0.30, cap 2.50) · gate step>=6x spread · window 22-06 UTC · 11+11 stops
(resting) · purge 5-vs-<=2 · trail arm 0.5 / giveback 0.3 · SL 8% of basis ·
pair cap 3 · 12% at last stop · daily breaker -$50 · startup cleanup.
Recommended balance >= $1,200 (maxDD -$808).
