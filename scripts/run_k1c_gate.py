#!/usr/bin/env python
"""V4-K1c (`docs/v4_spec.md` Sec7d, Revision 2, pre-registered
2026-08-18): the re-attempted K1 gate, using `BoundedIncidenceTopology
Rule` (`q=1/2`, `d_min=1`) instead of the original unconstrained
`RateBasedTopologyRule` that `[A57]`-`[A59]` found disconnects 10/10
lattices via genuine star-concentrated pruning.

Same frozen scale as the original K1 (`docs/v4_spec.md` Sec7/Sec11):
N=512, damage=10%, rho=0.01, m=3, eta=0.1, dt=0.05, K=50,
dtau_steps=50, 5 seeds, master_seed=20260818 -- SAME damaged lattices
as `[A57]`'s own run, only the topology rule differs.

Reports all three K1c-specific ICE gates (Sec7d) before trusting any
R_edge number, plus P5's cap-enforcement sanity check and regrowth-
concentration logging (Sec7d: "logged, never capped or pre-symmetrized").
"""

import sys

from boyko_benchmark.experiment.k1c_damage_gate import run_k1c_gate_one_seed
from boyko_benchmark.experiment.k1c_gate_verdict import aggregate_k1c_results

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_SEEDS = 5
DAMAGE_FRACTION = 0.10
RHO = 0.01
M_PERSISTENCE = 3
Q = 0.5  # docs/v4_spec.md Sec7d -- frozen, no exploratory calibration
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
DTAU_STEPS = 50
MASTER_SEED = 20260818  # identical to the original K1 -- SAME damaged lattices


def main() -> int:
    print("=== V4-K1c: bounded-incidence structural plasticity gate ===")
    print(
        f"N={N_SIDE_LENGTH**3}, damage_fraction={DAMAGE_FRACTION}, rho={RHO}, "
        f"m={M_PERSISTENCE}, q={Q}, eta={ETA}, dt={DT}, K={K_SUBSTEPS}, "
        f"dtau_steps={DTAU_STEPS}, {N_SEEDS} seeds, master_seed={MASTER_SEED}"
    )
    print()
    header = (
        f"{'seed':>4} {'n_damaged':>9} {'R_edge(A3)':>11} {'R_edge(A4)':>11} "
        f"{'trunc(A3)':>9} {'trunc(A4)':>9} {'max_prune(A3)':>14} {'max_prune(A4)':>14} "
        f"{'max_regrow(A3)':>15} {'max_regrow(A4)':>15}"
    )
    print(header)

    results = []
    for seed_index in range(N_SEEDS):
        result = run_k1c_gate_one_seed(
            side_length=N_SIDE_LENGTH,
            damage_fraction=DAMAGE_FRACTION,
            rho=RHO,
            m=M_PERSISTENCE,
            q=Q,
            eta=ETA,
            dt=DT,
            k=K_SUBSTEPS,
            dtau_steps=DTAU_STEPS,
            seed_index=seed_index,
            master_seed=MASTER_SEED,
        )
        results.append(result)
        max_prune_a3 = max((d.max_node_prune for d in result.arm_a3.diagnostics), default=0)
        max_prune_a4 = max((d.max_node_prune for d in result.arm_a4.diagnostics), default=0)
        max_regrow_a3 = max((d.max_node_regrow for d in result.arm_a3.diagnostics), default=0)
        max_regrow_a4 = max((d.max_node_regrow for d in result.arm_a4.diagnostics), default=0)
        trunc_a3 = str(result.arm_a3.truncated_at_window)
        trunc_a4 = str(result.arm_a4.truncated_at_window)
        print(
            f"{seed_index:>4} {len(result.damaged_out):>9} "
            f"{result.arm_a3.r_edge:>11.4f} {result.arm_a4.r_edge:>11.4f} "
            f"{trunc_a3:>9} {trunc_a4:>9} "
            f"{max_prune_a3:>14} {max_prune_a4:>14} {max_regrow_a3:>15} {max_regrow_a4:>15}"
        )

    verdict = aggregate_k1c_results(results, m=M_PERSISTENCE)

    print()
    print("=== V4-K1c ICE gates (Sec7d) ===")
    print(f"ICE-1 (exposure): {verdict.exposure_ratio:.3f} (threshold >= 0.95)")
    print(f"ICE-2 (disconnection rate): {verdict.disconnection_rate:.1%} (threshold <= 20%)")
    print(f"ICE-3 (cap activity, f_cap): {verdict.f_cap:.3f}")
    print(
        f"P5 sanity: max_i n_i^prune observed across the whole campaign = "
        f"{verdict.max_node_prune_ever} (expected <= 3 while degree stays at the "
        f"lattice's starting 6 -- see docs/assumptions.md for the degree-drift caveat)"
    )

    print()
    print(f"=== V4-K1c verdict: {verdict.status} ===")
    print(f"Reason: {verdict.reason}")
    if verdict.stats_a3 is not None and verdict.stats_a4 is not None:
        a3, a4 = verdict.stats_a3, verdict.stats_a4
        print(
            f"R_edge(A3): mean={a3.mean:.4f} std={a3.std:.4f} "
            f"CI=({a3.ci_95[0]:.4f},{a3.ci_95[1]:.4f})"
        )
        print(
            f"R_edge(A4): mean={a4.mean:.4f} std={a4.std:.4f} "
            f"CI=({a4.ci_95[0]:.4f},{a4.ci_95[1]:.4f})"
        )
        print(f"Cohen's d (A3 vs A4): {verdict.cohens_d:+.4f}")

    if verdict.status == "INVALID":
        print()
        print("INVALID -- substrate/ICE problem, NOT a K1c verdict. Do not read R_edge above")
        print("as evidence for or against the hypothesis.")
        return 2
    if verdict.status == "FAIL":
        print()
        print("K1c FAIL under a valid substrate => per the user's explicit instruction,")
        print("close V4 before M3. Do not propose K1d/K1e.")
        return 1

    print()
    print("K1c PASS -- proceed to M3 per docs/v4_spec.md Sec8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
