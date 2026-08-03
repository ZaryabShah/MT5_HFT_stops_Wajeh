"""v5 infinite-grid simulation (Wajeh's theory) over recorded ticks.

Rules: unlimited stop levels both sides at fixed spacing, positions accumulate,
NO purge/trail/pair-cap/equity-stop. Exit only at +target -> close all,
re-anchor. A drawdown abort (survival guard) records a "blow-up" instead of
letting the episode run unbounded — that's the statistic we care about.

Variant B: lot ladder — lot grows the deeper a level sits (x`ladder_mult`
every `ladder_every` levels, capped).
"""
from datetime import datetime, timezone

from backtest import build_seconds, minute_ranges  # reuse data pipeline


def lot_for(k, base, ladder_mult, ladder_every, lot_cap):
    if not ladder_mult:
        return base
    lot = base * (ladder_mult ** ((k - 1) // ladder_every))
    return min(lot, lot_cap)


def run_v5(secs, step=0.90, base_lot=0.01, target_usd=49.5, abort_dd=500.0,
           ladder_mult=None, ladder_every=3, lot_cap=0.08, gap=30):
    t = secs["t"]
    n = len(t)
    episodes = []
    i = 0
    idle_until = 0
    while i < n:
        if t[i] < idle_until:
            i += 1
            continue
        # new episode
        anchor_a, anchor_b = secs["ask_c"][i], secs["bid_c"][i]
        longs, shorts = [], []          # (entry, lot)
        nb = ns = 1
        ep_start = t[i]
        ep_min = 0.0
        outcome = None
        j = i + 1
        while j < n:
            ah, bl = secs["ask_h"][j], secs["bid_l"][j]
            ao, bo = secs["ask_o"][j], secs["bid_o"][j]
            bc, ac = secs["bid_c"][j], secs["ask_c"][j]
            while ah >= anchor_a + nb * step:
                lvl = anchor_a + nb * step
                longs.append((max(lvl, ao), lot_for(nb, base_lot, ladder_mult, ladder_every, lot_cap)))
                nb += 1
            while bl <= anchor_b - ns * step:
                lvl = anchor_b - ns * step
                shorts.append((min(lvl, bo), lot_for(ns, base_lot, ladder_mult, ladder_every, lot_cap)))
                ns += 1
            profit = sum((bc - e) * 100 * l for e, l in longs) \
                + sum((e - ac) * 100 * l for e, l in shorts)
            ep_min = min(ep_min, profit)
            if profit >= target_usd:
                outcome = "target"
            elif profit <= -abort_dd:
                outcome = "BLOWUP"
            if outcome:
                episodes.append(dict(outcome=outcome, pnl=profit, min_dd=ep_min,
                                     hours=(t[j] - ep_start) / 3600,
                                     fills=len(longs) + len(shorts), t=int(t[j])))
                idle_until = t[j] + gap
                i = j
                break
            j += 1
        else:
            # data ended mid-episode — record open state
            episodes.append(dict(outcome="OPEN_AT_END", pnl=profit, min_dd=ep_min,
                                 hours=(t[j - 1] - ep_start) / 3600,
                                 fills=len(longs) + len(shorts), t=int(t[j - 1])))
            break
        i += 1
    return episodes


def report(label, eps, target_usd, abort_dd):
    wins = [e for e in eps if e["outcome"] == "target"]
    blows = [e for e in eps if e["outcome"] == "BLOWUP"]
    openend = [e for e in eps if e["outcome"] == "OPEN_AT_END"]
    net = sum(e["pnl"] for e in eps)
    print(f"\n--- {label} (target +${target_usd}, abort -${abort_dd}) ---")
    print(f"episodes {len(eps)}: {len(wins)} wins, {len(blows)} BLOW-UPS, "
          f"{len(openend)} open at data end")
    print(f"net over 10 days: {net:+.2f}")
    if wins:
        hrs = sorted(e["hours"] for e in wins)
        print(f"time-to-target: median {hrs[len(hrs)//2]:.2f}h, max {hrs[-1]:.2f}h")
        dds = min(e["min_dd"] for e in wins)
        print(f"worst drawdown inside a WINNING episode: {dds:.2f}")
    for b in blows:
        print(f"  BLOWUP at {datetime.fromtimestamp(b['t'], tz=timezone.utc):%m-%d %H:%M} "
              f"after {b['hours']:.1f}h, {b['fills']} fills")
    for o in openend:
        print(f"  open at data end: P/L {o['pnl']:+.2f} (min {o['min_dd']:+.2f}), "
              f"{o['fills']} fills, {o['hours']:.1f}h in")


if __name__ == "__main__":
    secs = build_seconds()
    print(f"{len(secs['t']):,} seconds of data")

    eps = run_v5(secs, target_usd=49.5, abort_dd=500)
    report("A: flat 0.01 lots, $0.90 spacing", eps, 49.5, 500)

    eps = run_v5(secs, target_usd=120, abort_dd=500)
    report("A2: flat lots, bigger target ($120 = 12% of $1k)", eps, 120, 500)

    eps = run_v5(secs, target_usd=49.5, abort_dd=500, ladder_mult=1.3)
    report("B: lot ladder x1.3 every 3 levels (cap 0.08)", eps, 49.5, 500)

    eps = run_v5(secs, target_usd=120, abort_dd=500, ladder_mult=1.3)
    report("B2: ladder + bigger target", eps, 120, 500)
