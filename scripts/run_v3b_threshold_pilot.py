#!/usr/bin/env python
"""V3b (`null_results/20260814-open-system-geometrogenesis.md`, `[A51]`'s
own pre-registered next variant): does a threshold-based topology prune
-- which fires far more often than exact-zero pruning -- produce
structure the underpowered `[A51]` test could not detect?

Single assumption changed from `[A51]`'s V3 run: `PruneBelowThreshold
TopologyUpdate(threshold=0.01)` instead of `PruneZeroWeightTopology
Update`. Everything else identical (Cσ regime, N=512, 5 seeds,
HebbianAdaptation, localized psi0) -- same Minimal Relaxation discipline.

`threshold=0.01` is the exact value `[A51]` named in its own "If wrong"
clause before this script existed -- not chosen after seeing any
threshold-run data.
"""

import sys

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.dynamics.topology import PruneBelowThresholdTopologyUpdate
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.v3_topology_pilot import run_adaptive_dynamics_with_topology
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.observables.curvature import forman_ricci_curvature
from boyko_benchmark.statistics.cell_statistics import compute_cell_statistics

sys.path.insert(0, "scripts")
from run_phase12_strength_null import (  # noqa: E402
    global_shuffle,
    strength_stratified_shuffle,
)

N_SIZE = 512
N_SEEDS = 5
SIGMA_TILDE = 0.05
THRESHOLD = 0.01


def main() -> int:
    print("=== V3b: PruneBelowThresholdTopologyUpdate(threshold=0.01) on Csigma ===")
    print(f"N={N_SIZE}, {N_SEEDS} seeds, sigma_tilde={SIGMA_TILDE}, gamma=0, localized psi0")
    print()
    header = f"{'seed':>4} {'n_edges_before':>14} {'n_edges_after':>13} {'n_pruned':>9} "
    header += f"{'F_real':>10} {'exc_global':>11} {'exc_strat':>11}"
    print(header)

    glob_excess = []
    strat_excess = []
    total_pruned = 0
    for seed_index in range(N_SEEDS):
        graph_seed = 1000 * seed_index + N_SIZE
        graph = generate_erdos_renyi(N_SIZE, 3 * N_SIZE, np.random.default_rng(graph_seed))
        psi0 = localized_psi0(N_SIZE, source_node=0)
        n_before = int(graph.mask.sum()) // 2

        result = run_adaptive_dynamics_with_topology(
            graph,
            psi0,
            HebbianAdaptation(eta=0.1),
            PruneBelowThresholdTopologyUpdate(threshold=THRESHOLD),
            dt=0.05,
            k=50,
            dtau_steps=50,
            backend=PhenomenologicalOpenBackend(),
            gamma=0.0,
            sigma=SIGMA_TILDE,
            noise_seed=graph_seed,
        )
        g = result.final_graph
        n_after = int(g.mask.sum()) // 2
        n_pruned = n_before - n_after
        total_pruned += n_pruned

        finite_curvatures = forman_ricci_curvature(g)
        real = float(finite_curvatures.mean()) if len(finite_curvatures) else float("nan")
        e_glob = real - float(forman_ricci_curvature(global_shuffle(g, 900)).mean())
        e_strat = real - float(forman_ricci_curvature(strength_stratified_shuffle(g, 900)).mean())
        glob_excess.append(e_glob)
        strat_excess.append(e_strat)
        print(
            f"{seed_index:>4} {n_before:>14} {n_after:>13} {n_pruned:>9} "
            f"{real:>10.4f} {e_glob:>11.5f} {e_strat:>11.5f}"
        )

    print()
    print(f"Total edges pruned across {N_SEEDS} seeds: {total_pruned} / {N_SEEDS * (3 * N_SIZE)}")
    print()
    print("=== Structural excess under V3b (threshold pruning active) ===")
    g_stat = compute_cell_statistics(np.array(glob_excess))
    s_stat = compute_cell_statistics(np.array(strat_excess))
    g_zero = g_stat.ci_95[0] <= 0.0 <= g_stat.ci_95[1]
    s_zero = s_stat.ci_95[0] <= 0.0 <= s_stat.ci_95[1]
    g_ci = f"({g_stat.ci_95[0]:+.5f},{g_stat.ci_95[1]:+.5f})"
    s_ci = f"({s_stat.ci_95[0]:+.5f},{s_stat.ci_95[1]:+.5f})"
    print(f"  global-shuffle excess     = {g_stat.mean:+.5f} CI={g_ci}  contains 0: {g_zero}")
    print(f"  strength-strat excess     = {s_stat.mean:+.5f} CI={s_ci}  contains 0: {s_zero}")
    print()
    print("Reference, Csigma WITHOUT any pruning ([A43]/[A44]):")
    print("  global excess = +0.01577   strat excess = +0.01074")
    print("Reference, Csigma WITH exact-zero pruning ([A51], 1/7680 pruned):")
    print("  global excess = +0.01763   strat excess = +0.01013")
    return 0


if __name__ == "__main__":
    sys.exit(main())
