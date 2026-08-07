"""EXPERIMENT C — QUOTE SILENCE -> BURST (degraded: our export has 1-second
timestamps, so sub-second durations/Hawkes memory <1s are INVISIBLE; this
tests the whole-seconds version only). Silence = inter-tick gap >= G seconds
while the prior 60s was active (>=30 ticks). After quotes resume, measure the
first 2 seconds' net mid move; if |move| >= 0.10, signal continuation (or
fade) of the burst direction. Barrier race +-B as in experiments A/B."""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show

t, bid, ask = load()
n = len(t)
mid = (bid + ask) / 2
gap = np.diff(t, prepend=t[0])
cnt60 = np.arange(n) - np.searchsorted(t, t - 60)
spread_ok = (ask - bid) <= 0.12


def signals(G, fade):
    starts = np.flatnonzero((gap >= G) & (gap <= 600) & (cnt60 >= 30))
    sig = np.zeros(n, np.int8)
    for i in starts:
        j2 = np.searchsorted(t, t[i] + 2, "right") - 1
        if j2 <= i or not spread_ok[j2]:
            continue
        dm = mid[j2] - mid[i - 1]
        if abs(dm) < 0.10:
            continue
        d = 1 if dm > 0 else -1
        sig[j2] = -d if fade else d
    return sig, len(starts)


if __name__ == "__main__":
    header()
    best = None
    for G in (3, 5, 10):
        for fade in (False, True):
            sig, ns = signals(G, fade)
            mode = "fade" if fade else "cont"
            for B in (0.5, 1.0):
                r = run_sim(t, bid, ask, sig, B)
                show(f"G={G}s {mode} B={B} (sil={ns})", r)
                if best is None or r["net"] > best[3]["net"]:
                    best = (G, fade, B, r)
    G, fade, B, _ = best
    mode = "fade" if fade else "cont"
    print(f"\nhalves for best (G={G} {mode} B={B}):")
    sig, _ = signals(G, fade)
    a = run_sim(t, bid, ask, sig, B, t_to=MID_SPLIT)
    b = run_sim(t, bid, ask, sig, B, t_from=MID_SPLIT)
    print(f"  Apr-May: {a['net']:+.2f} ({a['n']} trd, {a['wres']:.1f}%) | "
          f"Jun-Jul: {b['net']:+.2f} ({b['n']} trd, {b['wres']:.1f}%)")
    print("\nDONE silence_burst")
