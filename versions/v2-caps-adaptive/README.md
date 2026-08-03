# v2 — Loss caps + adaptive step + fixed-lot test mode

**Ran:** Jul 30, 18:44–19:55 PKT · $120 top-up, later $1,200 more ($1,278.08)

## Added on top of v1
- **Pair cap** (`MAX_LOCKED_PAIRS = 3`): min(#longs, #shorts) ≥ 3 → flatten & re-anchor (locked pairs = frozen loss, only form in chop)
- **Equity stop** (`MAX_CYCLE_LOSS_PCT = 0.08`): cycle P/L ≤ −8% → flatten & re-anchor (pair cap bounds structure, not path risk)
- **Adaptive step** (`step = 0.5 × avg 5-bar M1 range`, floor $0.30) after $0.30 proved to be pure noise
- **Fixed-lot test mode** (`FIXED_TEST_LOT = 0.01`): targets/stops scale to a "virtual basis" (= balance for which 0.01 is the exact spec lot), so behavior matches full sizing in miniature; STATS lines carry pct-of-basis
- Bot loops forever (target/paircap/equitystop all re-anchor); stop-out detection; startup cleanup flattens leftovers

## Results
- At $0.30 step ($120): 1W/5L, $120 → $78.08 — caps worked but market 10× the grid scale
- First adaptive cycle (step $2.15, $1,278 balance): clean 10-level run peaked +$99.87
  on longs but ONE counter-side hedge (−$24.51) kept net at +$75, just under the
  +$96.52 target; reversal rode to −8% stop: **−$61.34**

## Lesson
The counter-side hedge is a parasite in a trend; profits must be banked when
trends fade → v3.
