"""Round 2: composite windows + robustness of the round-1 candidates.

Candidates from round 1 (each picked from ~50 cells -> selection bias, so
nothing is believed until it survives 5 start offsets):
  - window W1 = 20-22 U 00-06 (drop the dead/wide-spread 22-00 hours,
    add the profitable 20-22 block)
  - sl_pct 0.06 (made +3580 vs +3165 at 0.08 in round 1)
Also a few more composite windows for the plateau picture.
"""
from backtest import DEFAULT, minute_ranges, run
from trend_gate import er_series, move_series, secs

rng = minute_ranges(secs)
GATE = er_series(30, 0.25) & move_series(30, 3.0)

V47 = dict(DEFAULT)
V47.update(dict(sl_pct=0.08, trail_arm=0.5, trail_giveback=0.3, purge_at=5,
                step_cap=2.5, regime_mult=6.0, commission_per_lot_side=2.25,
                daily_stop=50, hours={22, 23, 0, 1, 2, 3, 4, 5},
                gate_series=GATE))

W1 = {20, 21, 0, 1, 2, 3, 4, 5}            # 20-22 U 00-06
W2 = {23, 0, 1, 2, 3, 4, 5}                # 23-06
W3 = {20, 21, 23, 0, 1, 2, 3, 4, 5}        # skip only 22
W4 = {0, 1, 2, 3, 4, 5}                    # 00-06


def show(label, r):
    nd = r["net"] / -r["max_dd"] if r["max_dd"] < 0 else float("inf")
    print(f"{label:<34}{r['net']:>+10.2f}{r['max_dd']:>+10.2f}{r['n']:>6}"
          f"{r['win_rate'] * 100:>5.0f}%{nd:>7.1f}", flush=True)


print("=== composite windows (full period) ===")
print(f"{'variant':<34}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}{'net/DD':>7}")
for label, hrs in [("20-22 U 00-06 (W1)", W1), ("23-06 (W2)", W2),
                   ("skip only 22 (W3)", W3)]:
    show(label, run(dict(V47, hours=hrs), secs, rng))

print("\n=== robustness: 5 start offsets ===")
t0 = int(secs["t"][0])
OFFS = [0, 3600, 10800, 25200, 46800]      # 0h, +1h, +3h, +7h, +13h
CANDS = [
    ("BASE 22-06 sl.08", dict(V47)),
    ("W1 sl.08", dict(V47, hours=W1)),
    ("00-06 sl.08", dict(V47, hours=W4)),
    ("BASE 22-06 sl.06", dict(V47, sl_pct=0.06)),
    ("W1 sl.06", dict(V47, hours=W1, sl_pct=0.06)),
]
for label, cfg in CANDS:
    nets, dds = [], []
    for off in OFFS:
        r = run(cfg, secs, rng, t_from=t0 + off)
        nets.append(r["net"])
        dds.append(r["max_dd"])
    print(f"{label:<20} nets: " + " ".join(f"{x:>+9.2f}" for x in nets))
    print(f"{'':<20} dds : " + " ".join(f"{x:>+9.2f}" for x in dds)
          + f"   | worst net {min(nets):+.2f}, worst DD {min(dds):+.2f}",
          flush=True)
print("\nDONE research_round2")
