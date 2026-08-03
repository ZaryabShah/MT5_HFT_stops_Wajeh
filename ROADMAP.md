# Roadmap — so nothing gets forgotten

_Last updated: Sat Aug 1, market closed. Account flat, $1,310.54. All version
history in [versions/](versions/)._

## Monday, at market open (~04:00 PKT)
1. **Launch v4.2** on Exness (`python bot.py` + monitor) — backtest-tuned
   config already staged in config.py (see versions/v4.2-backtest-tuned/):
   no cap, gate ON, SL 6%, giveback 0.4, purge 5. Backtested +$872/10d vs
   v4.1's −$1,438. ~~SL change~~ ~~trail review~~ — both settled by the sweep
4. **Fusion Markets live spread check** at open (demo measured avg $0.074 —
   verify live-session number; fusion_probe.py, run while Exness bot is DOWN
   or from second terminal — one terminal holds one account at a time)
5. **Second portable MT5 install** so Exness bot + Fusion account can run
   simultaneously

## This week
6. **v5 infinite-grid test** on Fusion demo — spec in versions/v5-infinite-grid/
   (base variant first, lot-ladder variant B after)
7. **Cap-theory verdict**: does v4.1's finding (skip-verdict cycles +$61 under
   the $0.90 cap) hold across a full week? stats.py tables decide
8. **Broker migration decision**: Fusion ~½ the round-trip cost of Exness
   Standard — if cap-theory holds, quiet-regime cycles benefit most
9. **Friday auto-flatten** as a proper bot feature (this week it was a manual
   sleep-script) — never hold grid positions into the weekend
10. **Windows autostart** (4 power cuts last week) — standing offer, needs
    Wajeh's go

## Parking lot
- Purge threshold 4 → 5 in mid-volatility (bounce-trap losses Jul 31 afternoon)
- Exness Raw Spread demo for a three-way broker comparison
- Sub-account / capital-split once a variant earns live-money consideration
