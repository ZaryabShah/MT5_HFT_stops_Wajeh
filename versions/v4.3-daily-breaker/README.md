# v4.3 — v4.2 + daily circuit breaker — STAGED for Monday Aug 3

One change vs v4.2: **`DAILY_STOP_USD = 50`** — once the UTC day's realized
P/L reaches −$50 (at 0.01 test lots), the bot goes flat until the next UTC day.

## Why (the Apr 6-17 autopsy)
The 4-month test exposed v4.2's blind spot: crisis-whipsaw regimes. Gold moved
$100–228/day with 3–6 direction changes; each swing filled 4-5 levels, the
purge committed, the swing reversed, the −6% stop fired — **158 equity stops
in two weeks, −$3,497**, on a fortnight the strategy churned 421 cycles.
Toxic days announce themselves with their first losses; quitting early skips
the other 13 stops of the day and forfeits little (bad days rarely turn good).

## Evidence (4 months, Fusion costs, 0.01 lots)
| | v4.2 | **v4.3 (stop $50)** |
|---|---|---|
| Net | +$973 | **+$1,861** |
| Max drawdown | −$4,178 | **−$1,251** |
| Apr 6–17 | −$3,497 | −$653 |
| Start-time robustness | 24/24 (10d test) | **5/5 over 4 months** (+$1,784…+$1,934, maxDD −$1,088…−$1,445) |

Threshold caveat: totals across $50/$75/$100 are path-noisy; the robust claim
is "a tight daily stop is structurally right," not "$50 is magic."

## Deployment notes
- Fusion account (mandatory — Standard's spread makes even v4.3 marginal)
- 0.01 lots; recommend Fusion demo balance ≥ $1,500 (4-month maxDD −$1,251)
- DAILY_STOP_USD is calibrated to 0.01 lots — rescale with lot size
