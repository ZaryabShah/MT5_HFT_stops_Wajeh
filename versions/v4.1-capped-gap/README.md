# v4.1 — Capped variable gap + 12% at the LAST stop  ← current version

**Ran:** Jul 31 22:00 – Aug 1 01:42 PKT (Friday close) · $1,291.15 → **$1,310.54**
Code snapshot in this folder (`bot.py`, `config.py`, `stats.py`) is the exact
running version.

## Changed vs v4 (all per Wajeh's spec)
- **`GRID_STEP_MAX = 0.90`** — gap stays volatility-adaptive but never wider
  than $0.90 (theory: big gaps were the problem, small capped gaps + trade
  everything beats sitting out)
- **`TARGET_LEVEL = 11`** — sizing delivers +12% exactly at the LAST stop;
  close the moment the last stop fills, never hold beyond it
- **Trade everything** (`REGIME_SHADOW_MODE = True`) — gate only tags verdicts
- `REGIME_WAIT_SEC = 120` (fast rechecks when gate is enforced)

## Results (6 cycles, Friday night)
−$7.81 (paircap), +$24.30 (last-stop), −$34.32 (equity stop), +$16.43 (trail),
+$17.40 (trail), +$10.93 (last-stop) = **+$26.93, 4W/2L**
(+$19.39 net of the −$7.54 mid-cycle transition flatten)

**Key finding:** the 5 skip-verdict cycles went 4W/1L **+$61** under the cap —
reversing the uncapped-era result (skips −$111). Early evidence Wajeh's
cap theory fixes the quiet regime rather than needing to skip it. One
trade-verdict cycle lost −$34. Needs a full week to confirm.

## Open questions for week 2
- Equity stop 8% → 6% (realized losses ≈ 2× realized wins; user wants smaller SL)
- Trail felt "too near" to the user — review with fresh data
- Does the cap finding hold outside a Friday-night sample?
