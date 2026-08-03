"""SpikeFader out-of-sample validation (Jul 29-31) + daily breakdown."""
from datetime import datetime, timezone

import numpy as np

from backtest import build_seconds
from strategies import precompute_move, respread, run_spikefader, split

base = build_seconds()
fusion = respread(base, 0.031)
CONFIGS = [(3.5, 1.0, 3.0, 300), (3.5, 1.0, 3.0, 120),
           (2.7, 1.0, 3.0, 120), (2.7, 1.0, 2.0, 300)]

print("=== OUT-OF-SAMPLE (Jul 29-31 — the wild days) ===")
for name, secs, comm in [("Fusion", fusion, 2.25), ("Standard", base, 0.0)]:
    oos = split(secs, False)
    mv = precompute_move(oos, 60)
    for f, tgt, stop, hold in CONFIGS:
        net, tr, w, dd = run_spikefader(oos, mv, f, tgt, stop, hold, comm)
        print(f"  {name:<9} F={f} tgt={tgt} stop={stop} hold={hold}: "
              f"net {net:+8.2f} | {tr} trades | {100*w/max(tr,1):.0f}% wins | maxDD {dd:+.2f}")

print("\n=== best config (F=3.5 tgt=1.0 stop=3.0 hold=300), Fusion, daily ===")
mv = precompute_move(fusion, 60)
t = fusion["t"]
days = np.unique(t // 86400)
for d in days:
    lo, hi = np.searchsorted(t, d * 86400), np.searchsorted(t, (d + 1) * 86400)
    if hi - lo < 1000:
        continue
    sub = {k: v[lo:hi] for k, v in fusion.items()}
    msub = mv[lo:hi]
    net, tr, w, dd = run_spikefader(sub, msub, 3.5, 1.0, 3.0, 300, 2.25)
    day = datetime.fromtimestamp(int(d * 86400), tz=timezone.utc).strftime("%a %m-%d")
    print(f"  {day}: net {net:+8.2f} | {tr:>3} trades | {100*w/max(tr,1):.0f}% wins | maxDD {dd:+.2f}")
