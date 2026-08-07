"""The clean IS/OOS protocol for the v5 hour discovery:
1) rank all hours on Apr-May ONLY (selection half)
2) test Apr-May's top-3 on Jun-Jul (untouched judge)
3) also: hours 18 & 20 (the full-period picks) on each half separately."""
from datetime import datetime, timezone

from v5_hourly import run

utc = timezone.utc
MID = int(datetime(2026, 6, 1, tzinfo=utc).timestamp())

print("=== hour ranking on Apr-May ONLY ===")
res = []
for h in range(1, 24):
    r = run(0.45, hours={h}, t_to=MID)
    res.append((h, r["net"], r["deaths"]))
res.sort(key=lambda x: -x[1])
for h, net, d in res[:5]:
    print(f"  top: hour {h:>2}  net {net:+.0f}  deaths {d}", flush=True)
for h, net, d in res[-3:]:
    print(f"  bottom: hour {h:>2}  net {net:+.0f}  deaths {d}")

print("\n=== Apr-May top-3 tested on Jun-Jul (true OOS) ===")
for h, _, _ in res[:3]:
    r = run(0.45, hours={h}, t_from=MID)
    print(f"  hour {h:>2} OOS: net {r['net']:+.0f} | deaths {r['deaths']} "
          f"| worst {r['worst']:+.0f}", flush=True)

print("\n=== full-period picks (18, 20) on each half ===")
for h in (18, 20):
    a = run(0.45, hours={h}, t_to=MID)
    b = run(0.45, hours={h}, t_from=MID)
    print(f"  hour {h}: Apr-May {a['net']:+.0f} ({a['deaths']}d) | "
          f"Jun-Jul {b['net']:+.0f} ({b['deaths']}d)", flush=True)
print("\nDONE v5_hour_split")
