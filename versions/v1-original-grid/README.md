# v1 — Original grid (Wajeh's spec, as dictated)

**Ran:** Jul 30, 17:53–17:58 PKT (two launches) · **Account:** Exness demo, $40

## Rules
- 11 buy stops above + 11 sell stops below anchor, fixed **$0.30** apart, after a 60s startup wait
- Lot sized so a straight run to level 10 = **+12%** of balance (min-lot floor: raw 0.0036 → forced 0.01 = 2.8× oversize)
- Close all at +12% → wait 30s → re-grid; if all 22 stops consumed → flatten and stop
- No other exits. No step adaptation. Magic 277888.

## What happened
Gold was moving $3–5/minute (extreme post-news tape). The ±$3.30 grid was consumed
almost instantly from both sides; hedged pairs locked losses; Exness stop-out
(`[so 0.00%...]`) zeroed the account in ~5 minutes across two runs.

## Cost anatomy of a full 22-stop double fill (measured)
- Locked hedge distance: ~$39.60 (83%) — structural, no broker can remove it
- Spread 22 × $0.24: ~$5.30 (11%) · Slippage: ~$3 (6%)

## Lesson
Step must scale with volatility; $0.24 spread is 80% of a $0.30 step; min-lot
floor distorts risk on small balances (balance ≈ 375 × step for exact sizing).
