# v4.8 — composite trading window 20-22 U 00-06 SERVER time — LAUNCH CONFIG

Product of the 08-03 variation sweep (user request: "check many variations —
targets, hours, compounding"). ~90 backtests, one survivor.

**Time basis:** all hours here are BROKER-SERVER hours (tick-timestamp basis,
GMT+3 in US summer) — real UTC equivalent (summer): 17-19 & effectively
22-03 (NY 1-3pm & 6-11pm; the nominal first hour, 21-22 UTC = server 0, is
the daily break and never trades). Wajeh's "doesn't the market close at 21 UTC?" question
exposed that bot.py compared TRADE_HOURS against machine UTC — a 3-hour
shift from the validated window. Fixed same day: bot.py server_time() reads
the clock from tick.time (also auto-idles the bot through the daily break,
weekends and holidays, since tick time freezes at close).

## The change
`TRADE_HOURS = {20, 21, 0, 1, 2, 3, 4, 5}` (was 22-06). The 24-cell hour
sweep showed the old window contained a dead zone and excluded a live one:
- server 20-22 standalone: **+$1,181** (net/DD 2.8) — was excluded
- server 22-00 standalone: **+$194** (~nothing) — was included; server 23 is
  the last hour before the 5pm-NY close, the day's widest spread ($0.118).
  Re-adding hour 23 to the new window costs −$1,352 on its own.
- server hour 0 = the daily break (zero ticks) — vacuous in the set.

## Evidence (real Fusion feed, 4 months, 0.01 lots)
| | v4.7 (22-06) | **v4.8 (20-22 U 00-06)** |
|---|---|---|
| Net | +$3,165 | **+$3,872** |
| Max drawdown | −$404 | **−$504** |
| Net per $ of DD | 7.8 | 7.7 |
| Cycles / win% | 572 / 53% | 607 / 54% |
| Worst of 5 start offsets | +$3,110 | **+$3,872** |
| Apr–May half | +$1,647 | **+$2,129** |
| Jun–Jul half | +$1,517 | **+$1,744** |

Wins all 5 start offsets AND both IS/OOS halves independently — the full
robustness protocol that killed v5, SAR and the sl=6% cell.

## What the same sweep rejected
- Every target from 3.3% to 17% (12%-at-L11 is the optimum, net/DD 7.8 vs
  ≤3.7 for all others).
- sl_pct 0.06 (+$3,580 alone, but neighbor 0.05 collapses and it HURTS
  combined with this window — improvements don't stack; 0.08 kept).
- 24h trading with the trend gate: +$1,242/−$862 — the gate cannot fix the
  06-20 UTC session (negative in every slice).
- Full-spec compounding (12% of balance per cycle): −78% peak-to-trough for
  the same final money as the tiered rule. Tiered daily lot
  (floor(bal/$1000) x 0.01) is the approved compounding path: $1k → $8,404
  on this sequence, never below $971.

## Caveats
Four stacked selections on the same 4 months now (params, session, gate,
window). The window was picked from ~50 candidates; offsets + half-split
reduce but don't eliminate selection bias. Live demo = the real judge;
optimistic benchmark ~$225/week at 0.01 lots.
