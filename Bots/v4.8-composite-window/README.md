# WajehGrid v4.8 — "Composite Window" (current validated build)

Self-contained package of the XAUUSD hedged-grid bot. v4.8 = v4.7 with ONE
change: the trading window is now the composite **20–22 ∪ 00–06 broker-server
time** (`TRADE_HOURS = {20, 21, 0, 1, 2, 3, 4, 5}`) instead of 22–06.

**Time basis (important):** all hours are BROKER-SERVER hours — the timestamp
basis of the tick data every backtest ran on (GMT+3 "NY-close" MT5 servers
during US summer), NOT real UTC. In real UTC (summer) the window is 17–19 &
effectively 22–03, i.e. New York 1–3 pm and 6–11 pm — the 21–22 UTC hour
inside the nominal range is the daily break (server hour 0, which never has
ticks, so it can never start a cycle). The bot reads the clock from tick
timestamps (`server_time()` in bot.py), so live behavior matches the
backtests exactly and survives US DST shifts. Server midnight = the daily
21:00-UTC break, so "hour 0" never actually trades.

Why the change: a 24-cell hour sweep on the real feed showed server 20–22 is
strongly profitable on its own (+$1,181) while server 22–00 earns nothing
(+$194 — server hour 23 is the last hour before the 5 pm NY close, the day's
widest spread at $0.118; re-adding that one hour costs −$1,352). So the
window swaps dead hours for live ones.

**Backtest (real FusionMarkets ticks, Apr 2 – Jul 31 2026, 0.01 lots):**
net **+$3,872**, max drawdown **−$504**, net/DD 7.7, 607 cycles, 54% wins —
vs v4.7's +$3,165 / −$404. Beats v4.7 on **all 5 start offsets** and on
**both data halves independently** (Apr–May: +$2,129 vs +$1,647; Jun–Jul:
+$1,744 vs +$1,517). Live will be humbler — treat **~$225/week** as the
optimistic benchmark.

---

## Files

| file | purpose |
|---|---|
| `bot.py` | the bot — run this |
| `config.py` | ALL settings + account credentials (edit here, never in bot.py) |
| `close_all.py` | emergency kill switch — cancels every pending, closes every position |
| `stats.py` | summarizes completed cycles from `bot.log` STATS lines |
| `requirements.txt` | Python dependency (MetaTrader5) |

`bot.log` is created next to `bot.py` on first run.

---

## Setup on a fresh machine

1. **Install the MetaTrader 5 terminal** (from your broker or metatrader5.com)
   and log it into the trading account **once manually** so the terminal knows
   the server. Leave the terminal installed (it can be closed; the Python API
   launches it).
2. **Install Python 3.10+ (Windows)** — the MetaTrader5 package is
   Windows-only.
3. `pip install -r requirements.txt`
4. Edit `config.py` top section: `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`,
   `SYMBOL`.
   - FusionMarkets demo: symbol is `XAUUSD` (this is the validated venue).
   - Exness: symbol is `XAUUSDm` (suffix!) — and Exness spread/commission was
     NOT what this config was tuned on. Re-validate before trusting it there.
5. Run: `python bot.py`
6. Stop: `Ctrl+C` stops the bot but **leaves orders/positions in place** —
   then run `python close_all.py` to flatten. (Or just run `close_all.py` any
   time; it only touches this bot's trades, magic 277888.)
7. Stats any time: `python stats.py`

**Recommended account: $1,000–1,200 balance per 0.01 lots.** Demo only unless
explicitly decided otherwise.

---

## Strategy — every rule, in fire order

**One cycle:**

1. **Anchor** at current price. Place **11 buy stops above** and **11 sell
   stops below**, evenly spaced.
2. **Adaptive spacing:** step = 0.5 × average range of the last 5 closed
   1-minute bars, floored at **$0.30**, capped at **$2.50** (the loose
   crisis-cap: tight caps ≤$1.50 are poison, but uncapped April steps of $5–8
   made single stops cost $140–220).
3. **Lot per level:** fixed **0.01** (test mode). Target/stop are computed
   against the "virtual basis" balance for which 0.01 is the exact spec size,
   so behavior is identical to full sizing, only in miniature.
4. **Orders are never re-placed mid-cycle.** A consumed side stays consumed.

**While the cycle runs, checks in priority order (every 0.5 s):**

1. **Profit target +12 %** of basis → close everything, wait 30 s, new cycle.
   (12 % is sized to land exactly at the 11th/last stop on a clean run.
   The 08-03 target sweep tested every alternative from 3.3 % to 17 % —
   12 %-at-last-stop beat them all decisively.)
2. **Trailing exit:** once profit has reached **50 %** of target, bank if it
   gives back **30 %** of target from the peak.
3. **Trend purge:** if one side has ≥ **5** fills while the other has ≤ 2,
   drop (close + cancel) the lagging side — bounce-trap protection.
4. **Equity stop −8 %** of basis → flatten, re-anchor. (6 % looked better in
   isolation but fails robustness when combined with the v4.8 window.)
5. **Pair cap:** ≥ **3** locked buy/sell pairs (chop signature) → flatten,
   re-anchor.
6. **All 22 stops consumed** → close everything, re-anchor.

**Before a new cycle may start (all must pass):**

1. **Trading window (v4.8):** new cycles only at broker-SERVER hours
   **20, 21, 00, 01, 02, 03, 04, 05** (read from tick time, not machine UTC)
   — the profitable band minus the dead server-22–00 gap. Open cycles always
   finish naturally.
2. **Trend gate (v4.7):** over the last **30 closed** M1 bars require BOTH
   efficiency ratio |net|/Σ|steps| ≥ **0.25** AND |net move| ≥ **$3.00**.
   No look-ahead: the forming bar is excluded. Recheck every 2 min.
3. **Daily circuit breaker:** once the UTC day's realized P/L hits
   **−$50**, flat until the next UTC day. Load-bearing, not insurance.
   **Calibrated to 0.01 lots — scale it with lot size.**
4. **Spread regime gate:** step must be ≥ **6×** the live spread, else sit out
   (recheck every 2 min).

**Housekeeping:** 60 s wait after start; 5 s wait between cycles (08-05: was
30 s — re-anchoring fast after a close rides trend continuation; +$4,374 /
−$341 vs +$3,872 / −$504 at 30 s, robust across offsets and halves); startup
flattens any leftovers from a previous run (power-cut safe); orders tagged
magic **277888** so the bot never touches other trades; terminal glitches
(`None` from the API) are never treated as "flat".

---

## Scaling up lots

Everything is exactly linear in lot size. Change **two** numbers in
`config.py`, together, plus fund the account accordingly:

| `FIXED_TEST_LOT` | `DAILY_STOP_USD` | recommended balance | 4-mo backtest net / maxDD |
|---|---|---|---|
| 0.01 | 50  | $1,000+ | +$3,872 / −$504 |
| 0.02 | 100 | $2,000+ | +$7,744 / −$1,007 |
| 0.03 | 150 | $3,000+ | +$11,617 / −$1,511 |

(0.02/0.03 rows are exact linear scalings — verified exact on the v4.7 runs.)

Compounding option (studied 08-03, not yet built into the bot): re-set lot
each UTC day to floor(balance / $1,000) × 0.01. On this 4-month sequence:
$1,000 → $8,404 without ever dipping below $971. Full-spec compounding
(12 % of balance every cycle) reaches the same place through a −78 %
drawdown — never use it.

---

## Hard-won warnings

- **Validated on FusionMarkets demo only** (real tick feed, ~$0.086 avg
  spread, $4.50/lot round-trip commission). A constant-spread model of this
  exact strategy was off by **$7,800** vs the real feed — do not assume it
  transfers to another broker without re-testing.
- Real ECN feeds have **spread-spike phantom fills** (ask jumps trigger buy
  stops with no price move). The 6×-spread gate and the $50 breaker exist
  because of this.
- The Exness **Real35 account is real money — read-only, never trade it**
  without an explicit human decision.
- Weekend: market closes Friday 21:00 real UTC (= Saturday 00:00 server) and
  reopens Monday 01:00 server time. Best practice: be flat over the weekend
  (`close_all.py` if a cycle is open). The bot idles through closes on its
  own — tick time freezes, which parks it outside the window.
- If the machine loses power mid-cycle, just restart the bot — startup
  cleanup flattens leftovers automatically.

---

## Lineage (why each rule exists)

v1 fixed grid → v2 adaptive step + caps → v3 purge/trail → v4 regime filter →
v4.1 capped gap → v4.2 backtest-tuned (purge 5, trail arm 0.5) → v4.3 daily
breaker → v4.4 crisis cap $2.50 → v4.5 real-feed retune (8 % stop, 0.3 trail,
6× spread gate) → v4.6 overnight window 22–06 → v4.7 trend gate
(ER ≥ 0.25 AND move ≥ $3 over 30 m) → **v4.8 composite window 20–22 ∪ 00–06
server time + server-clock fix** (the bot previously compared the window to
machine UTC — a 3-hour shift from the validated hours; caught 08-03 before
launch). Full research archive lives in the parent repo's `versions/` folder.
