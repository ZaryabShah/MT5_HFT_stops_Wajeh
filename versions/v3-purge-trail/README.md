# v3 — Trend purge + basket trail

**Ran:** Jul 30 19:58 – Jul 31 04:15 PKT (and as the "trade-everything" arm of
the Jul 31 shadow test) · started $1,215.76

## Added on top of v2
- **Trend purge** (`PURGE_OPPOSITE_AT = 4`): one side ≥ 4 fills while other ≤ 2 →
  close counter-side positions, cancel counter-side stops. Kills the hedge
  parasite while it's cheap.
- **Basket trail** (`TRAIL_ARM_FRAC = 0.5`, `TRAIL_GIVEBACK_FRAC = 0.3`): once
  net profit ≥ 50% of target, exit if it falls 30%-of-target below peak.

## Results
- US evening session: **9W/3L**, $1,215.76 → peak $1,412.93 (+16%) — every cycle
  shape (target, trail, paircap) behaving as designed
- Asian-session chop then bled 4 of 5 cycles (step shrank to ~$0.65 where the
  $0.24 spread = 37% drag; 4-fill "trends" were noise) → $1,337.42
- Full-day tagged comparison (Jul 31): trade-everything = 14W/16L, −$17 net,
  −17.6% compounded

## Lesson
The engine wins in trends and bleeds in quiet regimes — the regime is the
edge, not the grid → v4.
