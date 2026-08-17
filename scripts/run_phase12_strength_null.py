#!/usr/bin/env python
"""Phase 12 follow-up to `[A43]`: is the curvature signal geometric, or
just node-strength heterogeneity?

`[A43]` found that Forman-Ricci curvature has a nonzero structural excess
(F_real - F_weight_shuffled) that survives the `[A41]` global
weight-shuffle null model -- the first Phase 12 signal to do so
(d=3.103). It also named the leading mundane explanation and marked the
result `[HYPOTHESIS]` pending this test:

    Forman-Ricci contains 1/sqrt(w_e * w_neighbor), a nonlinear function
    of PAIRS of weights, so its expectation is not permutation-invariant
    whenever weights correlate with position. HebbianAdaptation's decay
    term is node-based (density[i] + density[j]), which by construction
    correlates the weights of all edges sharing a node. That alone would
    produce a nonzero excess with no geometric content.

The discriminator: a STRENGTH-STRATIFIED shuffle. Bin edges by the
product of their endpoints' node strengths, then permute weights only
WITHIN a bin. This preserves the weight-position relationship that node
strengths induce, while destroying any finer edge-level structure.

    excess_stratified ~= 0                  -> `[A43]` was node strengths
                                               all along; no edge-level
                                               structure; Stop Rule fires
    excess_stratified ~= excess_global      -> real edge-level structure
                                               beyond node strengths

Reported alongside the global-shuffle excess so the two are directly
comparable on the same graphs and seeds.
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
from boyko_benchmark.observables.curvature import forman_ricci_curvature
from boyko_benchmark.statistics.cell_statistics import cohens_d, compute_cell_statistics
from boyko_benchmark.types import WeightedGraph

N_SIZE = 512
N_SEEDS = 5
N_BINS = 20


def _rebuild(
    graph: WeightedGraph, upper: NDArray[np.integer], values: NDArray[np.floating]
) -> WeightedGraph:
    weights = np.zeros_like(graph.weights)
    for (i, j), value in zip(upper, values, strict=True):
        weights[i, j] = weights[j, i] = value
    return WeightedGraph(mask=graph.mask, weights=weights)


def global_shuffle(graph: WeightedGraph, seed: int) -> WeightedGraph:
    """`[A41]`'s null: permute weights across ALL edges."""
    rng = np.random.default_rng(seed)
    upper = np.argwhere(np.triu(graph.mask))
    values = np.array([graph.weights[i, j] for i, j in upper])
    rng.shuffle(values)
    return _rebuild(graph, upper, values)


def strength_stratified_shuffle(
    graph: WeightedGraph, seed: int, n_bins: int = N_BINS
) -> WeightedGraph:
    """Permute weights only among edges whose endpoint-strength product
    lands in the same quantile bin -- preserving what node strengths
    explain, destroying anything finer."""
    rng = np.random.default_rng(seed)
    upper = np.argwhere(np.triu(graph.mask))
    values = np.array([graph.weights[i, j] for i, j in upper])
    strength = graph.weights.sum(axis=1)
    keys = np.array([strength[i] * strength[j] for i, j in upper])

    # Quantile bins so each stratum holds a comparable number of edges
    # regardless of how skewed the strength-product distribution is.
    edges_of_bin = np.quantile(keys, np.linspace(0.0, 1.0, n_bins + 1))
    bin_index = np.clip(np.digitize(keys, edges_of_bin[1:-1]), 0, n_bins - 1)

    shuffled = values.copy()
    for b in range(n_bins):
        in_bin = np.flatnonzero(bin_index == b)
        if len(in_bin) > 1:
            permuted = rng.permutation(values[in_bin])
            shuffled[in_bin] = permuted
    return _rebuild(graph, upper, shuffled)


def _final_graph(seed_index: int, cell: str) -> WeightedGraph:
    graph_seed = 1000 * seed_index + N_SIZE
    graph = generate_erdos_renyi(N_SIZE, 3 * N_SIZE, np.random.default_rng(graph_seed))
    psi0 = localized_psi0(N_SIZE, source_node=0)
    backend = ClosedUnitaryBackend() if cell == "C0" else PhenomenologicalOpenBackend()
    sigma = 0.0 if cell == "C0" else 0.05
    noise_seed = None if cell == "C0" else graph_seed
    return run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        0.05,
        50,
        50,
        backend=backend,
        gamma=0.0,
        sigma=sigma,
        noise_seed=noise_seed,
    ).final_graph


def main() -> int:
    print("=== Phase 12 / [A43] follow-up: is the curvature signal geometric or node-strength? ===")
    print(f"N={N_SIZE}, {N_SEEDS} seeds, {N_BINS} strength-product bins")
    print()
    print(f"{'seed':>4} {'cell':>8} {'F_real':>10} {'excess_global':>14} {'excess_strat':>13}")

    global_excess: dict[str, list[float]] = {"C0": [], "Csigma": []}
    strat_excess: dict[str, list[float]] = {"C0": [], "Csigma": []}

    for seed_index in range(N_SEEDS):
        for cell in ("C0", "Csigma"):
            graph = _final_graph(seed_index, cell)
            real = float(forman_ricci_curvature(graph).mean())
            glob = float(forman_ricci_curvature(global_shuffle(graph, 900)).mean())
            strat = float(forman_ricci_curvature(strength_stratified_shuffle(graph, 900)).mean())
            global_excess[cell].append(real - glob)
            strat_excess[cell].append(real - strat)
            e_glob, e_strat = real - glob, real - strat
            print(f"{seed_index:>4} {cell:>8} {real:>10.4f} {e_glob:>14.5f} {e_strat:>13.5f}")

    print()
    print("=== Does the excess survive controlling for node strengths? ===")
    for cell in ("C0", "Csigma"):
        g_stat = compute_cell_statistics(np.array(global_excess[cell]))
        s_stat = compute_cell_statistics(np.array(strat_excess[cell]))
        s_contains_zero = s_stat.ci_95[0] <= 0.0 <= s_stat.ci_95[1]
        retained = 100.0 * s_stat.mean / g_stat.mean if g_stat.mean != 0 else float("nan")
        print(f"  {cell:>8}:")
        print(f"      global-shuffle excess    = {g_stat.mean:+.5f}  ([A43]'s number)")
        print(
            f"      strength-strat excess    = {s_stat.mean:+.5f}  "
            f"CI=({s_stat.ci_95[0]:+.5f},{s_stat.ci_95[1]:+.5f})  contains 0: {s_contains_zero}"
        )
        print(f"      retained after control   = {retained:.1f}% of the global excess")

    d_strat = cohens_d(np.array(strat_excess["Csigma"]), np.array(strat_excess["C0"]))
    print()
    print(f"  d(Csigma vs C0) on STRENGTH-CONTROLLED excess = {d_strat:.3f}")
    print("  ([A43]'s uncontrolled figure was d = 3.103)")
    print()
    print("If the strength-controlled excess collapses toward zero, [A43]'s signal was")
    print("node-strength heterogeneity with no edge-level geometric content, and Phase 12's")
    print("Stop Rule fires.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
