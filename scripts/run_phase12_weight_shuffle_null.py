#!/usr/bin/env python
"""Phase 12 decisive test (docs/phase12_spec.md, Stage 0 fallout): does
the Cσ modularity increase carry ANY structural information?

Background. Phase 12's Stage 0 substrate gate found that
`greedy_modularity_communities` is stable on graphs with genuine planted
communities (SBM: ARI=0.997 under a 1% weight perturbation) but chaotic
on the near-random graphs this project actually studies (ER: ARI=0.13;
cubic lattice: ARI=0.25). The detector is therefore sound -- the
partition simply is not a well-defined object on these graphs, the
classic degenerate-modularity-landscape phenomenon (Good, de Montjoye &
Clauset 2010). That makes phase12_spec.md's Stage 2 (which communities
formed?) unanswerable as specified, and raises a sharper question in its
place.

The test. Take each final graph and randomly permute its edge weights
across existing edges. This destroys every structural relationship by
construction while preserving the exact weight multiset. If
Q_real ~= Q_shuffled, then Q is a function of the weight DISTRIBUTION
alone and carries no structural content -- and the `[A37]`/`[A39]`
modularity finding, though a real and reproducible number, would not
mean the dynamics organized anything.

This is a stronger form of the H0 control from Phase 11 Milestone 5:
that one shuffled the correlation term *inside* the update rule and
compared scalars; this one shuffles the final structure itself and asks
whether the metric can tell the difference at all.
"""

import sys

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.observables.conductance import modularity
from boyko_benchmark.statistics.cell_statistics import cohens_d, compute_cell_statistics
from boyko_benchmark.types import WeightedGraph

N_SIZE = 512
N_SEEDS = 10
N_SHUFFLES = 3


def weight_shuffle(graph: WeightedGraph, seed: int) -> WeightedGraph:
    """Permute edge weights across existing edges: destroys all structure
    (which weight sits on which edge), preserves the exact multiset and
    the topology. The null model for "is Q structural or distributional?"
    """
    rng = np.random.default_rng(seed)
    upper = np.argwhere(np.triu(graph.mask))
    values = np.array([graph.weights[i, j] for i, j in upper])
    rng.shuffle(values)
    weights = np.zeros_like(graph.weights)
    for (i, j), value in zip(upper, values, strict=True):
        weights[i, j] = weights[j, i] = value
    return WeightedGraph(mask=graph.mask, weights=weights)


def _final_graph(seed_index: int, cell: str) -> WeightedGraph:
    graph_seed = 1000 * seed_index + N_SIZE
    graph = generate_erdos_renyi(N_SIZE, 3 * N_SIZE, np.random.default_rng(graph_seed))
    psi0 = localized_psi0(N_SIZE, source_node=0)
    if cell == "C0":
        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            HebbianAdaptation(eta=0.1),
            0.05,
            50,
            50,
            backend=ClosedUnitaryBackend(),
            gamma=0.0,
            sigma=0.0,
            noise_seed=None,
        )
    else:
        result = run_adaptive_dynamics_open(
            graph,
            psi0,
            HebbianAdaptation(eta=0.1),
            0.05,
            50,
            50,
            backend=PhenomenologicalOpenBackend(),
            gamma=0.0,
            sigma=0.05,
            noise_seed=graph_seed,
        )
    return result.final_graph


def main() -> int:
    print("=== Phase 12: weight-shuffle null model for the Cσ modularity effect ===")
    print(f"N={N_SIZE}, {N_SEEDS} seeds, {N_SHUFFLES} shuffles averaged per point")
    print()
    print(f"{'seed':>4} {'cell':>8} {'Q_real':>8} {'Q_shuf':>8} {'excess':>8} {'w_std':>8}")

    excess: dict[str, list[float]] = {"C0": [], "Csigma": []}
    q_real: dict[str, list[float]] = {"C0": [], "Csigma": []}
    w_std: dict[str, list[float]] = {"C0": [], "Csigma": []}

    for seed_index in range(N_SEEDS):
        for cell in ("C0", "Csigma"):
            graph = _final_graph(seed_index, cell)
            real = modularity(graph)
            shuffled = float(
                np.mean([modularity(weight_shuffle(graph, 900 + t)) for t in range(N_SHUFFLES)])
            )
            values: NDArray[np.floating] = graph.weights[np.triu(graph.mask)]
            std = float(values.std())
            q_real[cell].append(real)
            excess[cell].append(real - shuffled)
            w_std[cell].append(std)
            print(
                f"{seed_index:>4} {cell:>8} {real:>8.4f} {shuffled:>8.4f} "
                f"{real - shuffled:>8.4f} {std:>8.4f}"
            )

    print()
    print("=== Structural excess (Q_real - Q_shuffled): is ANY of Q structural? ===")
    for cell in ("C0", "Csigma"):
        stat = compute_cell_statistics(np.array(excess[cell]))
        contains_zero = stat.ci_95[0] <= 0.0 <= stat.ci_95[1]
        print(
            f"  {cell:>8}: mean={stat.mean:+.5f} "
            f"CI95=({stat.ci_95[0]:+.5f}, {stat.ci_95[1]:+.5f})  "
            f"CI contains 0: {contains_zero}"
        )

    d_excess = cohens_d(np.array(excess["Csigma"]), np.array(excess["C0"]))
    d_q = cohens_d(np.array(q_real["Csigma"]), np.array(q_real["C0"]))
    d_wstd = cohens_d(np.array(w_std["Csigma"]), np.array(w_std["C0"]))
    print()
    print("=== The comparison that decides it ===")
    print(f"  d(Csigma vs C0) on raw Q            = {d_q:8.3f}   <- [A37]/[A39]'s headline effect")
    print(f"  d(Csigma vs C0) on weight std       = {d_wstd:8.3f}   <- the distributional change")
    print(
        f"  d(Csigma vs C0) on STRUCTURAL excess= {d_excess:8.3f}   <- what survives the null model"
    )
    print()
    print("If the third number is near zero while the first two are large, the modularity")
    print("effect is entirely distributional: noise made weights heterogeneous, and a")
    print("heterogeneous-weight graph admits a higher-Q arbitrary partition. No organization.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
