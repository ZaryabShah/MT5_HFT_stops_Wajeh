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
| [v5](v5-infinite-grid/) | spec only — not yet run | infinite grid ± progressive lots | — |

## Balance timeline (real money on the demo)

$40 → $0 (v1) → +$120 → $78 (v2 @ $0.30 step) → +$1,200 = $1,278.08 (test mode
begins, 0.01 lots fixed) → $1,310.54 at Friday close.
Test-mode era: **44 cycles, 23W/21L, +$32.46 (+2.5%)**; full-size equivalent +2.6%.
Lifetime vs deposits ($1,360): −$49.46.
