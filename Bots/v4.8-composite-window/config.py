# MT5 account credentials and strategy configuration
# NOTE: Exness-MT5Trial16 is an Exness DEMO (trial) server.

# v4.5 launch target: FUSION demo (the only venue with a real-feed-validated
# profitable config). Exness trial kept for reference:
#   472305567 / Wajeh.277888 / Exness-MT5Trial16, symbol XAUUSDm
MT5_LOGIN = 426190
MT5_PASSWORD = "Kazmi@12345"
MT5_SERVER = "FusionMarkets-Demo"

SYMBOL = "XAUUSD"   # Fusion gold symbol (2-digit pricing)

# --- Grid geometry ---
GRID_STEP = 0.30          # $0.30 between levels (floor when ADAPTIVE_STEP is on)
GRID_LEVELS = 11          # 11 buy stops above + 11 sell stops below

# Volatility-adaptive step: a fixed $0.30 step is pure noise when gold moves
# $3-8/min (proven 2026-07-30: cycles resolved in seconds). Scale the step to
# recent 1-minute ranges so level 1 sits outside instantaneous noise.
ADAPTIVE_STEP = True
VOL_LOOKBACK_MIN = 5      # closed M1 bars to average
VOL_STEP_MULT = 0.5       # step = mult x avg 1-min range (floored at GRID_STEP)
# Cap history: TIGHT caps (<=1.50) are poison — they force the grid into
# noise (10-day sweep: cap 0.90 avg -$1,741; 4-month: cap 0.90 = -$3,371).
# But a LOOSE crisis-cap that only trims the extremes is a win: without it,
# April's $5-8 steps made single equity stops cost $140-220. 4-month test
# (with $50 breaker): cap 2.50 = +$2,291 / maxDD -$984 / April POSITIVE,
# vs no-cap +$1,861 / -$1,251 / April -$550. Robust 5/5 start times
# (maxDD identical -983.74 in every run). v4.4, staged 08-01 late.
GRID_STEP_MAX = 2.50
START_DELAY_SEC = 60      # wait 1 minute after bot start before placing grid
RESTART_DELAY_SEC = 30    # wait 30 seconds after profit-target close before restarting

# --- Test mode ---
# Trade this fixed lot regardless of balance (None = size from balance).
# Target/stop then scale to the "virtual basis" balance for which this lot IS
# the exact spec size — strategy behavior is identical to full sizing, only in
# miniature. STATS lines carry pct-of-basis so stats.py can compound what a
# fully-sized account would have done.
FIXED_TEST_LOT = 0.01

# --- Risk / target ---
PROFIT_TARGET_PCT = 0.12  # close everything at +12% of cycle-start balance
# Lot size is computed so that a clean one-directional run reaching the
# TARGET_LEVEL-th grid level yields PROFIT_TARGET_PCT of balance.
# User 08-01: 12% must land exactly at the LAST stop (close on last-stop hit,
# never hold beyond it) -> target level = last grid level.
TARGET_LEVEL = 11

# --- Option A: chop protection ---
# A "locked pair" = one buy AND one sell both filled; its loss is frozen forever.
# Locked pairs only form in chop, never in a clean trend. When this many pairs
# are locked: flatten everything, wait, re-anchor a fresh grid. 0 = disabled.
MAX_LOCKED_PAIRS = 3

# Equity backstop: pair cap bounds structure but not path risk (a run-then-
# reverse builds floating loss on unpaired positions before pairs lock).
# Flatten & re-anchor if cycle P/L <= -this fraction of cycle-start balance.
MAX_CYCLE_LOSS_PCT = 0.08  # v4.5: REAL-feed retune — 6% gets clipped by the
                           # noisier live feed; every profitable real-feed
                           # cell uses 8%

# v4.3 daily circuit breaker (Apr 6-17 autopsy: 158 equity stops in 2 weeks,
# -$3,497; toxic days announce themselves early). Once the UTC day's realized
# P/L hits -this, stop trading until the next UTC day. 4-month backtest:
# doubles net, cuts maxDD 70%; robust 5/5 start times. Value is calibrated to
# 0.01 test lots — rescale if lots ever change.
# v4.5: breaker back ON — the real-feed data ended the debate: ALL 10
# profitable real-feed configs have it; no-breaker lost $2.8-5.5k on the
# real feed. It is load-bearing, not insurance.
DAILY_STOP_USD = 50.0

# --- Regime filter (added 2026-07-31 ~04:15 after overnight chop bleed:
# Asian session shrank step to ~$0.65 where the $0.24 spread is a 37% drag and
# 4-fill "trends" are noise — 4 of 5 cycles lost). Sit out while the adaptive
# step is under this multiple of the live spread; recheck periodically.
# v4.7 trend gate (user's idea: classify movement first, trade only when
# trending). At cycle start, over the last 30 closed M1 bars require BOTH:
#   efficiency ratio |net|/sum|steps| >= 0.25  AND  |net move| >= $3.00
# Real-feed 4mo: +$3,165 / maxDD -$404 vs v4.6's +$1,857 / -$808.
# Robust: ER and move gates each 5/5 start times (4 byte-identical).
TREND_LOOKBACK_MIN = 30
TREND_ER_MIN = 0.25
TREND_MOVE_MIN = 3.0

# v4.6: trade ONLY overnight UTC (new cycles; open cycles finish naturally) —
# London/US hours LOSE even trend-gated (every 06-20 window negative).
# v4.8 (08-03): composite window 20-22 U 00-06. The 24-cell hour sweep showed
# 20-22 strongly positive (+$1,181 standalone) while 22-00 is dead (+$194;
# the 23 UTC rollover spread $0.118 is toxic — re-adding hour 23 alone costs
# -$1,352). Real-feed 4mo: +$3,872 / maxDD -$504 vs v4.7's +$3,165 / -$404.
# Robust: beats v4.7 on ALL 5 start offsets AND both IS/OOS halves.
TRADE_HOURS = {20, 21, 0, 1, 2, 3, 4, 5}

MIN_STEP_SPREAD_MULT = 6.0  # v4.5: stricter gate — on the variable real feed,
                            # quote-triggered stops need calmer-spread regimes
REGIME_WAIT_SEC = 120     # recheck the gate every 2 min
# Shadow mode (2026-07-31, user request): do NOT block trading; tag each cycle
# with the filter's would-be verdict instead, so stats.py can compare
# "v3 actual (all cycles)" vs "v4 simulated (only verdict=trade cycles)".
REGIME_SHADOW_MODE = False  # v4.2: gate ENFORCING — helps in live shadow test
                            # (+$67 vs -$44) AND in the 10-day sweep (gate-on
                            # beats gate-off on average across all 216 pairs).

# --- Trend protection (from cycle analysis 2026-07-30 19:55: a 10-level run
# peaked at +$75 net but one counter-side hedge cost $24.51 — the exact margin
# by which the target was missed — then the reversal rode to the -8% stop) ---
PURGE_OPPOSITE_AT = 5     # v4.2: 5 beats 4 in sweep (bounce-trap protection)
TRAIL_ARM_FRAC = 0.5      # arm trailing once net profit >= this frac of target
TRAIL_GIVEBACK_FRAC = 0.3 # v4.5: real-feed retune prefers the tighter trail

MAGIC = 277888            # order tag so the bot only touches its own trades
