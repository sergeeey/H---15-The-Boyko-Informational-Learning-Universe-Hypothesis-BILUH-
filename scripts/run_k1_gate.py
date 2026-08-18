#!/usr/bin/env python
"""M2 (`docs/v4_spec.md` Sec7/Sec8): the K1 damaged-lattice restoration
gate -- V4's cheap, pre-registered KILL GATE that must PASS before any
of M3-M6 proceed.

Take the T7/`[A32]` positive-control lattice (periodic cubic, N=512),
corrupt 10% of its edges via a degree-preserving rewire, then run V4's
`RateBasedTopologyRule` from that damaged graph with two regrow scorers:
A3 (`CorrelationScorer`, the real signal) and A4 (`DistanceStratified
ShuffleScorer`, the primary comparator). PASS requires `R_edge(A3) >
R_edge(A4)` on the aggregate mean across 5 seeds (`docs/v4_spec.md`
Sec7 -- a bare inequality, not an MCID gate; K1 is deliberately cheap
and easy to fail).

Parameters match this project's frozen defaults (`configs/development.
yaml`, `[A9]`): dt=0.05, K=50 fast-substeps/window, eta=0.1. dtau_steps
=50 matches Sec4's own calibration point ("cumulative turnover ~40%
over 50 windows" at rho=0.01) -- the same basis Sec11's "M2 K1 gate ...
~10 min compute" cost estimate uses.
"""

import sys

from boyko_benchmark.experiment.k1_damage_gate import run_k1_gate_one_seed
from boyko_benchmark.experiment.k1_gate_verdict import aggregate_k1_results

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_SEEDS = 5
DAMAGE_FRACTION = 0.10
RHO = 0.01
M_PERSISTENCE = 3
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
DTAU_STEPS = 50
MASTER_SEED = 20260818  # dated pre-registration, [A11] convention


def main() -> int:
    print("=== M2: K1 damaged-lattice restoration gate ===")
    print(
        f"N={N_SIDE_LENGTH**3}, damage_fraction={DAMAGE_FRACTION}, rho={RHO}, "
        f"m={M_PERSISTENCE}, eta={ETA}, dt={DT}, K={K_SUBSTEPS}, "
        f"dtau_steps={DTAU_STEPS}, {N_SEEDS} seeds, master_seed={MASTER_SEED}"
    )
    print()
    header = (
        f"{'seed':>4} {'n_damaged':>9} {'R_edge(A3)':>11} {'R_edge(A4)':>11} "
        f"{'wrong_rm(A3)':>13} {'wrong_rm(A4)':>13} {'trunc(A3)':>9} {'trunc(A4)':>9}"
    )
    print(header)

    results = []
    for seed_index in range(N_SEEDS):
        result = run_k1_gate_one_seed(
            side_length=N_SIDE_LENGTH,
            damage_fraction=DAMAGE_FRACTION,
            rho=RHO,
            m=M_PERSISTENCE,
            eta=ETA,
            dt=DT,
            k=K_SUBSTEPS,
            dtau_steps=DTAU_STEPS,
            seed_index=seed_index,
            master_seed=MASTER_SEED,
        )
        results.append(result)
        print(
            f"{seed_index:>4} {len(result.damaged_out_a3):>9} "
            f"{result.r_edge_a3:>11.4f} {result.r_edge_a4:>11.4f} "
            f"{result.wrong_removal_a3:>13.4f} {result.wrong_removal_a4:>13.4f} "
            f"{str(result.truncated_at_window_a3):>9} {str(result.truncated_at_window_a4):>9}"
        )

    verdict = aggregate_k1_results(results)
    print()
    print("=== K1 verdict ===")
    a3 = verdict.stats_a3
    a4 = verdict.stats_a4
    print(
        f"R_edge(A3): mean={a3.mean:.4f} std={a3.std:.4f} CI=({a3.ci_95[0]:.4f},{a3.ci_95[1]:.4f})"
    )
    print(
        f"R_edge(A4): mean={a4.mean:.4f} std={a4.std:.4f} CI=({a4.ci_95[0]:.4f},{a4.ci_95[1]:.4f})"
    )
    print(f"Cohen's d (A3 vs A4): {verdict.cohens_d:+.4f}")

    # docs/v4_spec.md Sec3 while-active ICE: rate > 20% of runs disconnecting
    # invalidates the whole grid -- rho itself must be re-pre-registered, not
    # patched. Counts BOTH arms' runs (2 * N_SEEDS total runs this gate makes).
    n_truncated = sum(
        1
        for r in results
        for t in (r.truncated_at_window_a3, r.truncated_at_window_a4)
        if t is not None
    )
    n_runs = 2 * N_SEEDS
    truncation_rate = n_truncated / n_runs
    print(f"ICE (disconnection) rate: {truncation_rate:.1%} ({n_truncated}/{n_runs} runs)")
    if truncation_rate > 0.20:
        print(
            "ICE rate exceeds 20% -- per docs/v4_spec.md Sec3, rho is too aggressive "
            "and this entire grid is INVALID, not just a caveat. Re-pre-register rho "
            "before trusting any R_edge number above."
        )
        return 2

    print(f"PASS (R_edge(A3) > R_edge(A4)): {verdict.passed}")
    if not verdict.passed:
        print()
        print("K1 FAIL => V4 STOPS HERE. Do not proceed to M3-M6 per docs/v4_spec.md Sec7.")
    return 0 if verdict.passed else 1


if __name__ == "__main__":
    sys.exit(main())
