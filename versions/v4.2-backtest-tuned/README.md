# v4.2 — Backtest-tuned config — STAGED for Monday Aug 3

Chosen from a 432-config sweep over 10 days of recorded ticks (Jul 20–31,
2.77M ticks, engine: backtest.py, results: sweep_results.csv). Config staged
in the live config.py; bot not yet run with it.

## Changes vs v4.1 (each backed by the sweep)
| Parameter | v4.1 | v4.2 | Evidence |
|---|---|---|---|
| `GRID_STEP_MAX` | 0.90 | **None** | cap 0.90 avg −$1,741 vs no-cap −$500 across ALL configs; v4.1 exact config replayed −$1,438/10d |
| `REGIME_SHADOW_MODE` | True (trade all) | **False (gate on)** | gate-on beats gate-off on average; live shadow test agreed (+$67 vs −$44) |
| `MAX_CYCLE_LOSS_PCT` | 0.08 | **0.06** | top-3 sweep rows all 0.06; also Wajeh's request |
| `TRAIL_GIVEBACK_FRAC` | 0.3 | **0.4** | giveback 0.4 dominates top rows — Wajeh's "trail too near" observation confirmed |
| `PURGE_OPPOSITE_AT` | 4 | **5** | 5 beats 4 in top rows (Jul 31 bounce-trap losses were 4th-fill entries) |

## Expected profile (backtest, 0.01 lots, 10 days)
Chosen row (sl .06 / arm .5 / gvbk .4 / purge 5 / no cap / gate 4×):
**net +$872, maxDD −$538, 266 cycles, 48% wins** — winners ~2× losers.
Reference: v4 as-was +$211; v3 −$205; v4.1 −$1,438.

## 2-month extended test (added later on Aug 1 — 14.5M ticks, Jun 1–Jul 31)
| Broker model | Net | maxDD | Weeks +/− |
|---|---|---|---|
| Exness Standard | **−$543** | −$2,375 | 4 / 5 |
| Fusion ECN | **+$3,078** | −$912 | 7 / 2 |

The June weeks were OUT-of-sample for the sweep tuning and the params held on
Fusion — real validation. But on Standard's $0.24 spread the calm weeks bleed
the strategy to a net loss: **cheap-spread execution is mandatory, not
optional.** Worst drawdown to expect at 0.01 lots: ~$900–1,000 (2.5-week
recovery); Fusion demo should hold ≥ $1,500.

## Honest caveats
- Tuned on 10 days, one instrument, including one abnormally volatile week;
  top-cell numbers are optimistic — the robust signal is the parameter
  DIRECTIONS (no tight cap, gate on, looser trail, purge 5), which hold
  across marginal averages, not just the best cells.
- Engine simplifications: 1s bars, fills at level price (gap-through at open),
  no queue slippage. Live results will differ in detail.
- Wajeh's cap theory tested fairly: it won its Friday-night sample (+$61 on
  skips) but loses decisively over 10 days — small samples mislead.
