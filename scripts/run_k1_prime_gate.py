#!/usr/bin/env python
"""V5-K1' (`docs/v5_spec.md` Sec7/Sec8 M2): the damaged-lattice
restoration gate for `BalancedSwapTopologyRule` -- V5's cheap,
pre-registered confirmatory test, run FIRST before any larger campaign.

Same T7/`[A32]` positive-control lattice and 10% degree-preserving
damage as V4's K1/K1c/K1d (N=512, `master_seed=20260818`), now paired
with A3 (`CorrelationSwapScorer`, state-driven swap) vs A4
(`DistanceStratifiedSwapScorer`, matched-null swap).

Swap budget calibrated per `docs/assumptions.md` `[A65]` (measured
compute cost, not tuned after any result): `n_swaps=3`/window,
`dtau_steps=10`, matching `docs/v5_spec.md` Sec11's corrected estimate
(~6 minutes for the full 5-seed campaign).
"""

import sys

from boyko_benchmark.experiment.k1_prime_damage_gate import run_k1_prime_gate_one_seed
from boyko_benchmark.experiment.k1_prime_gate_verdict import aggregate_k1_prime_results

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_SEEDS = 5
DAMAGE_FRACTION = 0.10
N_SWAPS = 3  # docs/assumptions.md [A65] -- compute-calibrated, not exploratory
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
DTAU_STEPS = 10  # docs/assumptions.md [A65]
MASTER_SEED = 20260818  # identical to K1/K1c/K1d -- SAME damaged lattices


def main() -> int:
    print("=== V5-K1': balanced support rewiring damaged-lattice gate ===")
    print(
        f"N={N_SIDE_LENGTH**3}, damage_fraction={DAMAGE_FRACTION}, n_swaps={N_SWAPS}, "
        f"eta={ETA}, dt={DT}, K={K_SUBSTEPS}, dtau_steps={DTAU_STEPS}, {N_SEEDS} seeds, "
        f"master_seed={MASTER_SEED}"
    )
    print()
    header = (
        f"{'seed':>4} {'n_damaged':>9} {'R_edge(A3)':>11} {'R_edge(A4)':>11} "
        f"{'commit(A3)':>10} {'skip(A3)':>9} {'commit(A4)':>10} {'skip(A4)':>9}"
    )
    print(header)

    results = []
    for seed_index in range(N_SEEDS):
        result = run_k1_prime_gate_one_seed(
            side_length=N_SIDE_LENGTH,
            damage_fraction=DAMAGE_FRACTION,
            n_swaps=N_SWAPS,
            eta=ETA,
            dt=DT,
            k=K_SUBSTEPS,
            dtau_steps=DTAU_STEPS,
            seed_index=seed_index,
            master_seed=MASTER_SEED,
        )
        results.append(result)
        print(
            f"{seed_index:>4} {len(result.damaged_out):>9} "
            f"{result.arm_a3.r_edge:>11.4f} {result.arm_a4.r_edge:>11.4f} "
            f"{result.arm_a3.total_committed:>10} {result.arm_a3.total_skipped:>9} "
            f"{result.arm_a4.total_committed:>10} {result.arm_a4.total_skipped:>9}"
        )

    verdict = aggregate_k1_prime_results(results)

    print()
    print("=== V5-K1' verdict ===")
    a3, a4 = verdict.stats_a3, verdict.stats_a4
    print(
        f"R_edge(A3): mean={a3.mean:.4f} std={a3.std:.4f} CI=({a3.ci_95[0]:.4f},{a3.ci_95[1]:.4f})"
    )
    print(
        f"R_edge(A4): mean={a4.mean:.4f} std={a4.std:.4f} CI=({a4.ci_95[0]:.4f},{a4.ci_95[1]:.4f})"
    )
    print(f"Cohen's d (A3 vs A4): {verdict.cohens_d:+.4f}")
    print(f"K_skip rate: {verdict.k_skip_rate:.1%} (warn threshold: {0.20:.0%})")
    if verdict.weak_flag:
        print("K_skip exceeds 20% -- R_edge above is flagged [WEAK], not fully trusted.")

    print()
    print(f"Verdict: {verdict.status} (R_edge(A3) > R_edge(A4)): {verdict.status == 'PASS'}")
    if verdict.status == "FAIL":
        print()
        print("K1' FAIL => per docs/v5_spec.md Sec7, stop before any larger campaign.")
    else:
        print()
        print("K1' PASS -- V5 proceeds to a larger campaign (not yet specified, Sec8 M3+).")
    return 0 if verdict.status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
