"""Does DRIFT-B survive realistic entries? Tick-exact (real spreads),
Apr-Jul 2026: enter at fixed delays after 01:00, or at first spread<=X,
exit at real bid ~05:59. Commission included."""
import numpy as np

z = np.load("data/secs_fusion.npz")
t = z["t"].astype(np.int64)
bid_c, ask_c = z["bid_c"], z["ask_c"]
spread = ask_c - bid_c
days = np.unique(t // 86400)


def replay(entry_rule):
    net, n, costs = 0.0, 0, []
    for d in days:
        e0 = d * 86400 + 1 * 3600
        x0 = d * 86400 + 6 * 3600
        i1 = np.searchsorted(t, x0) - 1
        if i1 <= 0 or x0 - t[i1] > 600:
            continue
        i0 = entry_rule(d, e0)
        if i0 is None or i0 >= i1:
            continue
        net += (bid_c[i1] - ask_c[i0]) - 0.045
        costs.append(spread[i0])
        n += 1
    return net, n, (np.mean(costs) if costs else 0)


def fixed_delay(sec):
    def rule(d, e0):
        i = np.searchsorted(t, e0 + sec)
        return i if i < len(t) and t[i] - (e0 + sec) < 300 else None
    return rule


def spread_trigger(maxspr, deadline=1800):
    def rule(d, e0):
        i = np.searchsorted(t, e0)
        while i < len(t) and t[i] - e0 < deadline:
            if spread[i] <= maxspr:
                return i
            i += 1
        return None
    return rule


print(f"{'entry rule':<26}{'net 4mo':>9}{'days':>6}{'avg entry spread':>18}")
for lbl, rule in (
    ("first tick (naive)", fixed_delay(0)),
    ("+2 min", fixed_delay(120)),
    ("+5 min", fixed_delay(300)),
    ("+10 min", fixed_delay(600)),
    ("+15 min", fixed_delay(900)),
    ("spread<=0.15", spread_trigger(0.15)),
    ("spread<=0.10", spread_trigger(0.10)),
):
    net, n, avgspr = replay(rule)
    print(f"{lbl:<26}{net:>+9.2f}{n:>6}{avgspr:>18.3f}", flush=True)
print("\nDONE drift_entry_test")
