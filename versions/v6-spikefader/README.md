# v6 — SpikeFader (data-mined candidate) — backtest only, not yet live

Found Aug 1 by measuring the tape first (characterize.py): gold's 1-minute
spikes mean-revert (~$0.16 giveback after $2.70+ spikes), strongest signal in
the whole dataset at second scales.

## Rules
- If price moved **≥ $3.50 in the last 60s** → fade it (spike up = sell,
  spike down = buy), market entry
- Take profit **+$1.00**, stop loss **−$3.00**, max hold **300s**
- One position at a time, 0.01 lots

## Results (10 days of ticks, Fusion cost model: $0.062 spread + commission)
- **+$45.03 total, 1,616 trades, 76% wins, maxDD −$76**
- 9 of 11 days positive; one bad day (Thu 07-30 extreme session) −$56
- On Exness Standard's $0.24 spread: NEGATIVE — Fusion/raw-type account only
- IS (+$72 Jul 20-28) held direction OOS but the wild Jul 29-31 days net −$26
- Volatility-veto variants (skip fades during big 15-min moves): tested,
  made it WORSE (−$12 to −$22) — hypothesis falsified, keep it simple

## Honest assessment
- Edge per trade ≈ +$0.028 after costs → borderline statistical significance
  (~2σ on 1,616 trades). Real but thin.
- Biggest unmodeled risk: **entry slippage** — it market-buys/sells seconds
  after a violent spike, the worst moment for fills. Live edge will be
  thinner than sim; could be zero. Demo test is the only way to know.
- ~$4.5/day at 0.01 lots. Scales linearly only if execution holds.

## Graveyard from the same research day
- SAR stop-and-reverse: −$437 to −$57k across all distances/brokers — dead
- TrendRider (15-min momentum entry + trail): −$130 to −$180 IS — the
  measured continuation exists but naive threshold entries buy local tops
