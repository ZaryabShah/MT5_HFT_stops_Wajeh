"""Week-by-week ledger for v5-restart on the REAL Fusion feed.
Rules: start with $1,000. Grid levels every X dollars, both sides, unlimited.
Close all at +$49.5 (target hit = 'win'), re-anchor. If equity hits ~$0 the
account is DEAD: deposit a fresh $1,000 and restart. Bank compounds within a
life; a death loses the entire current bank."""
from datetime import datetime, timedelta, timezone

from backtest import build_seconds

COMM_HALF = 0.0225
TARGET = 49.5
BANK0 = 1000.0
DEATH = 10.0


def run_ledger(secs, step):
    t = secs["t"]
    n = len(t)
    bank = BANK0
    deposits = 1
    weeks = {}      # monday -> dict(wins, deaths, min_eq, end_bank, end_net)
    deaths_log = []
    life_start = int(t[0])
    life_peak = BANK0
    longs, shorts = [], []
    nb = ns = 1
    anchor_a = anchor_b = None
    idle_until = 0
    j = 0

    def wk_of(ts):
        d = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        return (d - timedelta(days=d.weekday())).strftime("%m-%d")

    while j < n:
        wk = wk_of(t[j])
        w = weeks.setdefault(wk, dict(wins=0, deaths=0, min_eq=1e18,
                                      end_bank=bank, end_net=0.0))
        if anchor_a is None:
            if t[j] >= idle_until:
                anchor_a, anchor_b = secs["ask_c"][j], secs["bid_c"][j]
                longs, shorts = [], []
                nb = ns = 1
            j += 1
            continue
        ah, bl = secs["ask_h"][j], secs["bid_l"][j]
        ao, bo = secs["ask_o"][j], secs["bid_o"][j]
        bc, ac = secs["bid_c"][j], secs["ask_c"][j]
        while ah >= anchor_a + nb * step:
            longs.append(max(anchor_a + nb * step, ao))
            bank -= COMM_HALF
            nb += 1
        while bl <= anchor_b - ns * step:
            shorts.append(min(anchor_b - ns * step, bo))
            bank -= COMM_HALF
            ns += 1
        profit = sum(bc - e for e in longs) + sum(e - ac for e in shorts)
        equity = bank + profit
        w["min_eq"] = min(w["min_eq"], equity)
        life_peak = max(life_peak, equity)
        if profit >= TARGET:
            bank += profit - COMM_HALF * (len(longs) + len(shorts))
            w["wins"] += 1
            anchor_a = None
            idle_until = t[j] + 30
        elif equity <= DEATH:
            deaths_log.append(dict(t=int(t[j]), days=(t[j] - life_start) / 86400,
                                   peak=life_peak))
            w["deaths"] += 1
            bank = BANK0
            deposits += 1
            life_start = int(t[j])
            life_peak = BANK0
            anchor_a = None
            idle_until = t[j] + 30
        w["end_bank"] = bank + profit if anchor_a is not None else bank
        w["end_net"] = w["end_bank"] - BANK0 * deposits
        j += 1
    return weeks, deaths_log, deposits, bank


secs = build_seconds("data/ticks_fusion.npz", "data/secs_fusion.npz")
for step in (0.45, 0.30):
    weeks, deaths, deposits, bank = run_ledger(secs, step)
    print(f"\n================ v5-restart, spacing ${step} ================")
    print(f"{'week':<7}{'wins':>5}{'deaths':>7}{'lowest eq':>10}{'bank end':>10}"
          f"{'net-to-date':>12}")
    for wk in sorted(weeks):
        w = weeks[wk]
        print(f"{wk:<7}{w['wins']:>5}{w['deaths']:>7}{w['min_eq']:>10.2f}"
              f"{w['end_bank']:>10.2f}{w['end_net']:>+12.2f}")
    print(f"deposits used: {deposits} x $1,000 | final bank {bank:.2f} | "
          f"NET {bank - deposits * BANK0:+.2f}")
    if deaths:
        print("death events:")
        for d in deaths:
            print(f"  {datetime.fromtimestamp(d['t'], tz=timezone.utc):%a %m-%d %H:%M} UTC "
                  f"— life lasted {d['days']:.1f} days, peaked at {d['peak']:.2f}")
    else:
        print("no deaths — the first $1,000 survived the whole 4 months")
