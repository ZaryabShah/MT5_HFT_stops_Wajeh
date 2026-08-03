# Version archive — Wajeh XAUUSD grid bot

Every strategy version we've tested, one folder each: what it was, how it ran,
what it made. Full code snapshots exist from v4.1 onward (earlier versions were
edited in place before we started archiving; their READMEs document the exact
config instead).

| Version | Period (PKT) | Idea | Result |
|---|---|---|---|
| [v1](v1-original-grid/) | Jul 30, 17:53–17:58 | Original fixed $0.30 grid | $40 → $0 (stop-out, ~5 min) |
| [v2](v2-caps-adaptive/) | Jul 30, 18:44–19:55 | + pair cap, equity stop, adaptive step, test mode | $120→$78 at $0.30; then $1,278→$1,217 |
| [v3](v3-purge-trail/) | Jul 30 19:58 – Jul 31 04:15 | + trend purge + basket trail | $1,216→peak $1,413→$1,337 |
| [v4](v4-regime-filter/) | Jul 31 04:15–21:35 | + regime gate (step ≥ 4× spread) | shadow: +$67 vs −$44; live 5 cyc ±$0 |
| [v4.1](v4.1-capped-gap/) | Jul 31 22:00 – Aug 1 01:42 | + $0.90 gap cap, 12% at LAST stop | 6 cyc, 4W/2L, **+$26.93** |
| [v4.2](v4.2-backtest-tuned/) | staged Aug 1 | sweep-tuned: SL 6%, purge 5, no cap | +$872/10d (modeled) |
| [v4.3](v4.3-daily-breaker/) | staged Aug 1 | + $50/day circuit breaker | +$1,861/4mo (modeled) |
| [v4.4](v4.4-crisis-cap/) | staged Aug 1 | + loose $2.50 step cap | +$2,291/4mo (modeled) |
| [v4.5](v4.5-real-feed/) | staged Aug 2 | retuned on REAL Fusion ticks (SL 8%) | **+$1,507/4mo real feed** |
| [v4.6](v4.6-overnight/) | staged Aug 2 | + window 22-06 UTC | +$1,857 / −$808 real |
| [v4.7](v4.7-trend-gate/) | staged Aug 2 | + trend gate ER≥0.25 & move≥$3/30m | +$3,165 / −$404 real |
| [v4.8](v4.8-composite-window/) | staged Aug 3 | window → 20-22 ∪ 00-06 UTC | **+$3,872 / −$504 real — LAUNCH** |
| [v5](v5-infinite-grid/) | closed Aug 3 | infinite grid ± restarts — lottery, all filters fail | do not revisit |
| [v6](v6-spikefader/) | archived Aug 1 | fade ≥$3.5/60s spikes | +$45/10d, thin, shelved |

## Balance timeline (real money on the demo)

$40 → $0 (v1) → +$120 → $78 (v2 @ $0.30 step) → +$1,200 = $1,278.08 (test mode
begins, 0.01 lots fixed) → $1,310.54 at Friday close.
Test-mode era: **44 cycles, 23W/21L, +$32.46 (+2.5%)**; full-size equivalent +2.6%.
Lifetime vs deposits ($1,360): −$49.46.
