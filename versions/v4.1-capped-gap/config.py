# MT5 account credentials and strategy configuration
# NOTE: Exness-MT5Trial16 is an Exness DEMO (trial) server.

MT5_LOGIN = 472305567
MT5_PASSWORD = "Wajeh.277888"
MT5_SERVER = "Exness-MT5Trial16"

SYMBOL = "XAUUSDm"  # Exness standard-account gold symbol

# --- Grid geometry ---
GRID_STEP = 0.30          # $0.30 between levels (floor when ADAPTIVE_STEP is on)
GRID_LEVELS = 11          # 11 buy stops above + 11 sell stops below

# Volatility-adaptive step: a fixed $0.30 step is pure noise when gold moves
# $3-8/min (proven 2026-07-30: cycles resolved in seconds). Scale the step to
# recent 1-minute ranges so level 1 sits outside instantaneous noise.
ADAPTIVE_STEP = True
VOL_LOOKBACK_MIN = 5      # closed M1 bars to average
VOL_STEP_MULT = 0.5       # step = mult x avg 1-min range (floored at GRID_STEP)
# User 08-01: cap the placed gap — variable below the cap, never wider.
# The regime gate still judges the RAW (uncapped) volatility number.
GRID_STEP_MAX = 0.90
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
MAX_CYCLE_LOSS_PCT = 0.08

# --- Regime filter (added 2026-07-31 ~04:15 after overnight chop bleed:
# Asian session shrank step to ~$0.65 where the $0.24 spread is a 37% drag and
# 4-fill "trends" are noise — 4 of 5 cycles lost). Sit out while the adaptive
# step is under this multiple of the live spread; recheck periodically.
MIN_STEP_SPREAD_MULT = 4.0
REGIME_WAIT_SEC = 120     # user 08-01: recheck the gate every 2 min, not 10
# Shadow mode (2026-07-31, user request): do NOT block trading; tag each cycle
# with the filter's would-be verdict instead, so stats.py can compare
# "v3 actual (all cycles)" vs "v4 simulated (only verdict=trade cycles)".
REGIME_SHADOW_MODE = True   # user 08-01: back to trade-everything (v3 logic)
                            # with the new GRID_STEP_MAX cap; verdicts still
                            # tagged so the gate question re-tests under the cap.
                            # (Uncapped 07-31 test: skips went 4W/9L, -$111.)

# --- Trend protection (from cycle analysis 2026-07-30 19:55: a 10-level run
# peaked at +$75 net but one counter-side hedge cost $24.51 — the exact margin
# by which the target was missed — then the reversal rode to the -8% stop) ---
PURGE_OPPOSITE_AT = 4     # one side >= this many fills (other <= 2): close/cancel other side
TRAIL_ARM_FRAC = 0.5      # arm trailing once net profit >= this frac of target
TRAIL_GIVEBACK_FRAC = 0.3 # then exit if profit falls this frac of target below peak

MAGIC = 277888            # order tag so the bot only touches its own trades
