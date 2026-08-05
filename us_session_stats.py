"""WHY the bot fails in the US session: per-hour tape anatomy.
For each server hour: total path traveled per 30min vs net displacement
(efficiency), trend-gate pass rate, avg spread, avg 1-min range."""
import numpy as np

from trend_gate import secs

t = secs["t"].astype(np.int64)
hour = (t // 3600) % 24
mid = (secs["bid_c"] + secs["ask_c"]) / 2
spr = secs["ask_c"] - secs["bid_c"]

mins = t // 60
uniq, idx = np.unique(mins, return_index=True)
bounds = np.append(idx, len(t))
m_close = mid[bounds[1:] - 1]
m_hour = (uniq * 60 // 3600) % 24
m_range = np.array([mid[bounds[i]:bounds[i + 1]].max()
                    - mid[bounds[i]:bounds[i + 1]].min()
                    for i in range(len(uniq))])
absdiff = np.abs(np.diff(m_close, prepend=m_close[0]))

# 30-min windows: net vs path
net30 = np.abs(m_close[30:] - m_close[:-30])
path30 = np.array([absdiff[i - 30:i].sum() for i in range(30, len(m_close))])
h30 = m_hour[30:]
er30 = np.where(path30 > 1e-9, net30 / path30, 0)

print(f"{'server hr':>9}{'avg 1m range':>13}{'avg spread':>11}{'path/30m':>10}"
      f"{'net/30m':>9}{'ER':>6}{'gate-pass%':>11}")
for h in list(range(20, 24)) + list(range(0, 20)):
    m = m_hour == h
    m3 = h30 == h
    sec_m = hour == h
    if not m3.any():
        continue
    gate = (er30[m3] >= 0.25) & (net30[m3] >= 3.0)
    print(f"{h:>9}{m_range[m].mean():>13.2f}{spr[sec_m].mean():>11.3f}"
          f"{path30[m3].mean():>10.2f}{net30[m3].mean():>9.2f}"
          f"{er30[m3].mean():>6.2f}{100 * gate.mean():>10.1f}%", flush=True)
print("\nDONE us_session_stats")
