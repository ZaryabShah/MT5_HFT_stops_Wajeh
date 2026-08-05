"""Corrected fade small-target test: genuine target_mult (dollar target =
mult x mirrored target) + faster trend-abort. Least-bad cell: 06-12 ANTI."""
from fade_day import ANTI, run_fade, wrap
import fade_day as fd

# patch: wrap run_fade with a real target multiplier via module constant
import numpy as np  # noqa: F401


def run_mult(hours, gate, mult, abort_at):
    """Re-run fade with target scaled by mult (monkey-level: temporary
    replacement of target inside a copied loop is overkill — instead use
    target_pct scaling identity: target$ = LOT*C*step*55; to scale by m,
    scale levels' triangular factor via target_pct AND sl_pct together so
    SL dollars stay put while target shrinks."""
    # target$ = basis*target_pct, basis = base$/target_pct -> basis changes,
    # so to get target$ = m*base$ with SL$ unchanged:
    #   target_pct' = 0.12 (any), basis' = base$/0.12 ... unreachable via pct.
    # Clean approach: run_fade exposes target_pct and sl_pct; basis' scales
    # 1/target_pct'. Choose target_pct' = 0.12/m -> basis' = m*basis,
    # target$' = basis'*pct' = base$  ... still pinned. So instead scale via
    # LEVELS in the triangular number: target$ ~ levels*(levels-1). Use the
    # levels param ONLY for sizing (ladder depth stays 11 in run_fade's lists
    # because they use the same levels arg — accept shallower ladder too:
    # a small-target fade wants a shallow ladder anyway).
    lv = {0.25: 5, 0.5: 8, 1.0: 11}[mult]
    return run_fade(hours, gate=gate, levels=lv, abort_at=abort_at,
                    abort_other=min(2, abort_at - 1))


if __name__ == "__main__":
    H = wrap(6, 12)
    print(f"{'variant':<40}{'net':>10}{'maxDD':>10}{'cyc':>6}{'win%':>6}")
    for mult, abort in ((0.25, 5), (0.5, 5), (1.0, 3), (0.5, 3), (0.25, 3)):
        net, dd, n, w = run_mult(H, ANTI, mult, abort)
        print(f"fade 06-12 ANTI tgt x{mult} abort{abort}"
              f"{'':<8}{net:>+10.2f}{dd:>+10.2f}{n:>6}"
              f"{100 * w / max(n, 1):>5.0f}%", flush=True)
    print("\nDONE fade_fix")
