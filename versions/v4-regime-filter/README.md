# v4 — Regime filter (sit out dead markets)

**Ran:** Jul 31 04:15–21:35 PKT (04:20–18:00 in shadow mode, 18:01–21:34 enforcing)

## Added on top of v3
- **Regime gate** (`MIN_STEP_SPREAD_MULT = 4`): only place a grid while the
  adaptive step ≥ 4× the live spread; otherwise wait and recheck
  (`REGIME_WAIT_SEC`, 600 then 120)
- **Shadow mode** (`REGIME_SHADOW_MODE`): trade everything but tag each cycle's
  STATS line `regime=trade|skip` so v3-vs-v4 compares exactly on the same market

## Results (Jul 31 shadow test, 19 tagged cycles, uncapped step era)
| Arm | Cycles | Record | Net | Compounded |
|---|---|---|---|---|
| v3 trade-everything | 19 | 8W/11L | −$44.33 | −20.0% |
| v4 filtered | 6 | 4W/2L | **+$66.82** | **+17.9%** |
| skipped pile | 13 | 4W/9L | −$111.15 | −32.1% |

Enforcing run (Fri evening): 5 cycles, 2W/3L, ±$0, then gate correctly closed
for the quiet evening.

## Lesson
Removing a reliably-losing regime is real value — but see v4.1: capping the
gap may fix those quiet cycles instead of skipping them.
