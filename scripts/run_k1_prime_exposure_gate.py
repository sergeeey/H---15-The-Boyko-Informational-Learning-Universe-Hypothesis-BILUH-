#!/usr/bin/env python
"""`V5-K1'-Exposure` (`docs/v5_spec.md` Sec13): the frozen dose-response
follow-up to `K1'` -- was `[A66]`'s weak result compute-starvation, or
does state-driven selection genuinely not beat the matched null even at
`B=D` (as many committed swaps as damaged edges)?

Frozen parameters (Sec13.1, `[A67]`): `n_swaps=3`/window (unchanged from
K1'), checkpoints at window counts `{10,25,49}` (nominal committed swaps
`≈{30,75,147}` against `D≈148`), `N_seeds=10` (decided from a real
timing probe, `[A67]`, before any `R_edge` from this follow-up was
seen), same T7/`[A32]` lattice, same 10% damage, same
`master_seed=20260818` convention (seeds 0-4 are the SAME damaged
lattices as `K1'` itself; seeds 5-9 are new, deterministic extensions of
the same seed stream).
"""

import sys

from boyko_benchmark.experiment.k1_prime_exposure_gate import run_k1_prime_exposure_gate_one_seed
from boyko_benchmark.experiment.k1_prime_exposure_verdict import aggregate_k1_prime_exposure_results

N_SIDE_LENGTH = 8  # N = 8^3 = 512
N_SEEDS = 10  # docs/assumptions.md [A67] -- decided from measured timing, not reactive
DAMAGE_FRACTION = 0.10
N_SWAPS = 3  # docs/v5_spec.md Sec13.1 -- unchanged from K1'
CHECKPOINT_WINDOWS = (10, 25, 49)  # docs/v5_spec.md Sec13.1's frozen schedule
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
MASTER_SEED = 20260818  # identical to K1/K1c/K1d/K1' -- seeds 0-4 are the SAME damaged lattices


def main() -> int:
    print("=== V5-K1'-Exposure: dose-response follow-up to K1' ===")
    print(
        f"N={N_SIDE_LENGTH**3}, damage_fraction={DAMAGE_FRACTION}, n_swaps={N_SWAPS}, "
        f"checkpoints={CHECKPOINT_WINDOWS}, eta={ETA}, dt={DT}, K={K_SUBSTEPS}, "
        f"{N_SEEDS} seeds, master_seed={MASTER_SEED}"
    )
    print()

    results = []
    for seed_index in range(N_SEEDS):
        result = run_k1_prime_exposure_gate_one_seed(
            side_length=N_SIDE_LENGTH,
            damage_fraction=DAMAGE_FRACTION,
            n_swaps=N_SWAPS,
            checkpoint_windows=CHECKPOINT_WINDOWS,
            eta=ETA,
            dt=DT,
            k=K_SUBSTEPS,
            seed_index=seed_index,
            master_seed=MASTER_SEED,
        )
        results.append(result)
        print(f"--- seed {seed_index} (n_damaged={len(result.damaged_out)}) ---")
        header = (
            f"{'window':>7} {'R_edge(A3)':>11} {'R_edge(A4)':>11} "
            f"{'cum_commit(A3)':>15} {'cum_skip(A3)':>13} "
            f"{'cum_commit(A4)':>15} {'cum_skip(A4)':>13}"
        )
        print(header)
        for cp3, cp4 in zip(result.arm_a3.checkpoints, result.arm_a4.checkpoints, strict=True):
            print(
                f"{cp3.window_count:>7} {cp3.r_edge:>11.4f} {cp4.r_edge:>11.4f} "
                f"{cp3.cumulative_committed:>15} {cp3.cumulative_skipped:>13} "
                f"{cp4.cumulative_committed:>15} {cp4.cumulative_skipped:>13}"
            )
        print()

    assert len(results) == N_SEEDS, (
        f"expected {N_SEEDS} completed seeds before aggregating, got {len(results)} -- "
        f"a partial/crashed campaign must not silently produce a verdict at the wrong "
        f"n_seeds (reviewer-flagged, docs/v5_spec.md Sec13.3's n_seeds caution applies)."
    )
    verdict = aggregate_k1_prime_exposure_results(results)

    print("=== V5-K1'-Exposure verdict: ΔR(B) dose-response curve ===")
    curve_header = (
        f"{'window':>7} {'R_edge(A3)':>11} {'R_edge(A4)':>11} {'delta_R':>9} "
        f"{'cohens_d':>9} {'mcid_pass':>10} {'wins_A3':>8} {'majority':>9}"
    )
    print(curve_header)
    for cp in verdict.checkpoints:
        print(
            f"{cp.window_count:>7} {cp.stats_a3.mean:>11.4f} {cp.stats_a4.mean:>11.4f} "
            f"{cp.delta_r_mean:>9.4f} {cp.cohens_d:>9.4f} {str(cp.mcid_pass):>10} "
            f"{cp.seeds_a3_beats_a4:>3}/{cp.n_seeds:<4} {str(cp.majority_a3_beats_a4):>9}"
        )

    primary = verdict.checkpoints[-1]
    print()
    print(f"Primary checkpoint (B=D, window={primary.window_count}):")
    print(
        f"  R_edge(A3): mean={primary.stats_a3.mean:.4f} std={primary.stats_a3.std:.4f} "
        f"CI=({primary.stats_a3.ci_95[0]:.4f},{primary.stats_a3.ci_95[1]:.4f})"
    )
    print(
        f"  R_edge(A4): mean={primary.stats_a4.mean:.4f} std={primary.stats_a4.std:.4f} "
        f"CI=({primary.stats_a4.ci_95[0]:.4f},{primary.stats_a4.ci_95[1]:.4f})"
    )
    print(
        f"  Cohen's d: {primary.cohens_d:+.4f}  "
        f"MCID pass (|d|>=0.8, non-overlapping CI): {primary.mcid_pass}"
    )
    print(
        f"  Seeds A3>A4: {primary.seeds_a3_beats_a4}/{primary.n_seeds}  "
        f"Majority: {primary.majority_a3_beats_a4}"
    )
    print()
    print(f"Verdict: {verdict.status}")
    if verdict.status == "FAIL":
        print()
        print(
            "docs/v5_spec.md Sec13.4's frozen stop-rule applies: no automatic "
            "2D/5D/10D follow-up. A further budget increase requires a new, "
            "separately-motivated pre-registration."
        )
    return 0 if verdict.status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
