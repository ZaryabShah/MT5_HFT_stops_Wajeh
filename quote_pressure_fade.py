"""Experiment A follow-up: FADE the extreme quote-pressure cells (the 32.8%
continuation win at N=100 X=0.6 implies ~67% for the fade — but n=64 and the
control baseline is 43.7%, so this is a mirage check, run on BOTH extreme
cells and both halves before believing anything)."""
import numpy as np

from microlab import MID_SPLIT, header, load, run_sim, show
from quote_pressure import filt, imbalance

t, bid, ask = load()
n = len(t)

if __name__ == "__main__":
    header()
    for N, X in ((100, 0.6), (50, 0.6), (100, 0.5)):
        imb = imbalance(N)
        sig = np.zeros(n, np.int8)
        sig[imb >= X] = -1          # inverted: fade the pressure
        sig[imb <= -X] = 1
        sig[~filt] = 0
        for B in (0.5, 1.0):
            r = run_sim(t, bid, ask, sig, B)
            show(f"FADE N={N} X={X} B={B}", r)
            a = run_sim(t, bid, ask, sig, B, t_to=MID_SPLIT)
            b = run_sim(t, bid, ask, sig, B, t_from=MID_SPLIT)
            print(f"    halves: Apr-May {a['net']:+.2f} ({a['n']}) | "
                  f"Jun-Jul {b['net']:+.2f} ({b['n']})", flush=True)
    print("\nDONE quote_pressure_fade")
