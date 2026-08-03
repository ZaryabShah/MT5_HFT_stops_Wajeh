# v4.5 — first config validated on REAL feed data — MONDAY LAUNCH

The turning point: Wajeh exported 1GB of genuine Fusion Markets ticks
(24.6M ticks, Apr 2 – Jul 31). The real feed **invalidated the respread
model** (finalized v4.4-nb config: modeled +$2,262 → real −$5,544, blown up
Apr 10). Causes: real avg spread $0.086 (not 0.062) + variable-spread wicks
triggering resting stops (phantom fills, ~$2.8k of damage).

## Config changes vs v4.4 (from a 48-config re-tune ON the real feed)
| Parameter | old | v4.5 | Why |
|---|---|---|---|
| `MAX_CYCLE_LOSS_PCT` | 0.06 | **0.08** | noisy real feed clips 6% stops |
| `TRAIL_GIVEBACK_FRAC` | 0.4 | **0.3** | real-feed retune |
| `MIN_STEP_SPREAD_MULT` | 4.0 | **6.0** | resting stops need calm-spread regimes |
| `DAILY_STOP_USD` | None (user pref) | **50** | ALL 10 profitable real-feed cells have it; not optional |
| account | Exness trial | **Fusion demo 426190** | real Exness feed: every variant negative (spread too big) |
| `GRID_STEP_MAX` | 2.50 | 2.50 | unchanged |

## Evidence (real Fusion feed, 4 months, 0.01 lots, $2.25/side commission)
- **+$1,507, maxDD −$1,195, 1,317 cycles, 49% wins**
- Robustness: 5/5 start times +$1,433…+$1,568, maxDD identical every run
- MID-trigger variant (+$1,644) exists but needs bot rework; deferred
- Exness real feed same window: best variant −$846 — venue dead

## Honest caveats
- The 4 months of real data were used for selection → +$1,507 is in-sample;
  expect less live. The demo run IS the out-of-sample test: compare weekly
  vs ~$85/week backtest average.
- Recommend Fusion demo balance ≥ $1,500 (real-feed maxDD −$1,195 at 0.01).
