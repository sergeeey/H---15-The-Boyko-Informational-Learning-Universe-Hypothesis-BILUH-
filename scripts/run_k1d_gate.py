#!/usr/bin/env python
"""V4-K1d (`docs/v4_spec.md` Sec7e, Revision 3, pre-registered
2026-08-18): the re-attempted K1 gate, identical to K1c except `b_i` is
computed from each node's REFERENCE degree (captured once, immediately
after lattice damage, before any dynamics run) instead of its CURRENT
degree -- breaks `[A60]`'s diagnosed feedback loop (uncapped regrowth
inflating a node's degree, which inflated its own future cap).

Same frozen scale, same `q=1/2` (no new calibration -- `[A61]`'s exact
capacity audit confirmed the K1c bottleneck is structural, not
algorithmic, so a smaller `q` would only worsen it), same damaged
lattices as K1c/K1/`[A57]`: N=512, damage=10%, rho=0.01, m=3, eta=0.1,
dt=0.05, K=50, dtau_steps=50, 5 seeds, master_seed=20260818.

Reports ICE-1/ICE-2/ICE-3 (Sec7d, unchanged) plus P5's cap-enforcement
check and regrowth-concentration logging, exactly as K1c did.
"""

import sys

from boyko_benchmark.experiment.k1c_damage_gate import run_k1c_gate_one_seed
from boyko_benchmark.experiment.k1c_gate_verdict import aggregate_k1c_results

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_SEEDS = 5
DAMAGE_FRACTION = 0.10
RHO = 0.01
M_PERSISTENCE = 3
Q = 0.5  # docs/v4_spec.md Sec7e -- unchanged from K1c, no new calibration
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
DTAU_STEPS = 50
MASTER_SEED = 20260818  # identical to K1/K1c -- SAME damaged lattices


def main() -> int:
    print("=== V4-K1d: reference-degree incidence cap gate ===")
    print(
        f"N={N_SIDE_LENGTH**3}, damage_fraction={DAMAGE_FRACTION}, rho={RHO}, "
        f"m={M_PERSISTENCE}, q={Q}, eta={ETA}, dt={DT}, K={K_SUBSTEPS}, "
        f"dtau_steps={DTAU_STEPS}, {N_SEEDS} seeds, master_seed={MASTER_SEED}, "
        f"use_reference_degrees=True"
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
            use_reference_degrees=True,
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
    print("=== V4-K1d ICE gates (Sec7d, unchanged formulas) ===")
    print(f"ICE-1 (exposure): {verdict.exposure_ratio:.3f} (threshold >= 0.95)")
    print(f"ICE-2 (disconnection rate): {verdict.disconnection_rate:.1%} (threshold <= 20%)")
    print(f"ICE-3 (cap activity, f_cap): {verdict.f_cap:.3f}")
    print(
        f"P5 sanity: max_i n_i^prune observed across the whole campaign = "
        f"{verdict.max_node_prune_ever} (expected <= 3 always now -- reference degree "
        f"cannot drift above the lattice's starting 6, unlike K1c)"
    )

    print()
    print(f"=== V4-K1d verdict: {verdict.status} ===")
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
        print("INVALID -- substrate/ICE problem, NOT a K1d verdict. Do not read R_edge above")
        print("as evidence for or against the hypothesis. Per docs/v4_spec.md Sec7e: if even")
        print("the exact optimum (not just this greedy run) cannot reach 0.95 exposure under")
        print("the reference-degree cap, that is a new finding requiring the same [A61]-style")
        print("capacity audit before any further pre-registration.")
        return 2
    if verdict.status == "FAIL":
        print()
        print("K1d FAIL under a valid substrate => per the user's standing instruction,")
        print("close V4 before M3. Do not propose a further variant.")
        return 1

    print()
    print("K1d PASS -- proceed to M3 per docs/v4_spec.md Sec8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
