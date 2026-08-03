# v5 — Infinite grid (Wajeh's theory) — SPEC, not yet run

## The idea (as Wajeh described it, Aug 1)
Unlimited buy stops above and sell stops below, some fixed distance apart —
levels never run out. Never stop, never re-anchor. Only exit: total profit
reaches the target (e.g. +12%). Claim: the only losing path is "all of one
side then all of the other" — and with unlimited levels there is no "all",
so eventually some excursion is big enough and we always win.

**Upgrade variant:** lots grow with depth (small at first levels, bigger the
further price runs), so after a whipsaw the recovery side wins back the locked
losses quickly.

## The honest math
- **The claim is TRUE with unlimited budget.** Gold's price wanders far enough,
  often enough, that a big one-directional excursion eventually arrives; profit
  on an excursion grows with its square (k levels ≈ k²·step/2 per lot), so it
  eventually outruns any accumulated locked losses. With infinite capital the
  target is hit with probability ~1.
- **The cost is unbounded drawdown while waiting.** Every buy+sell pair that
  both trigger locks a permanent loss. Chop keeps locking pairs. Measured on
  our own Friday data (~$0.90 spacing, 0.01 lots): one full up-down oscillation
  locks roughly $25–30; five hours of chop locked >$130. The account must
  SURVIVE the wait — and any finite balance has a real chance of stop-out
  before the winning excursion arrives.
- This is the **martingale / Zone-Recovery family**: many small-to-medium wins,
  rare account-killing loss. It doesn't remove the risk of ruin — it moves it
  into a fat tail. Expected profit per month can look great right up until the
  one ranging fortnight that takes 100%.
- **The lot-scaling upgrade makes both effects stronger**: recovery is faster
  AND drawdown becomes explosive instead of linear. The tail gets fatter.

## Why we'll still test it (on demo)
Wajeh explicitly wants it explored; demo cost is zero; gold in this era trends
hard (helps this strategy) — worth measuring: win frequency, max drawdown per
cycle, time-to-target, and how often it survives a week.

## Planned config
- Spacing: fixed $0.90 (same as v4.1 cap) · Base lot 0.01
- Levels placed as a rolling window (broker limits pending orders — keep ~15
  per side live, add deeper ones as price approaches the edge)
- Exit: net P/L ≥ 12% of basis; hard abort if drawdown ≥ 50% of allocated
  balance (survival guard — records "would have blown up" without wasting the
  account)
- Variant B: lot ladder ×1.3 every 3 levels deep, hard-capped
- Run on the **Fusion Markets demo** (second portable MT5 install) so it can't
  interfere with v4.1 on Exness and tests Fusion's ~$0.07 spread live
