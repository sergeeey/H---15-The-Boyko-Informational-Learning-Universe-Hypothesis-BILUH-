#!/usr/bin/env python
"""K1 concentration + permutation-equivariance audit (user-directed,
2026-08-18, extending `[A58]`). Still feasibility-only: no R_edge/G1/
curvature, no scientific outcome.

Two questions, in order:

1. Per-node prune-concentration distribution at window 2 (all 5 seeds,
   same damaged lattices as `[A57]`/`[A58]`): full histogram, top-1/
   top-3 share of all deletions, Gini/HHI, and -- for the single most-
   affected node -- its pre-prune degree, strength (sum of incident
   weights), own density, and mean |correlation| over its own incident
   edges. Also counts DISTINCT weight values among existing edges right
   before pruning: if far fewer than the edge count, many edges are
   EXACTLY tied, and Python's stable `sorted()` would break those ties
   by original list order (`np.argwhere(np.triu(mask))`'s ascending
   node-index order) -- a label-dependent artifact hiding inside a
   supposedly weight-driven selection.

2. The decisive red-team check: permutation equivariance. `V4` claims a
   physical mechanism, so relabeling nodes (`G -> PGP^T`, `psi -> P*psi`)
   must not change WHICH PHYSICAL LOCATION gets concentrated-pruned --
   only its label. Seed 0's damaged lattice is relabeled via a random
   permutation, the identical window-0..2 sequence is rerun with the
   SAME seeds, and the pruned-edge set (mapped back through the
   permutation) is compared against the original run's pruned-edge set.

Kill criterion (user's own framing): if relabeling changes WHICH
physical region gets pruned, this is a tie-break/ordering IMPLEMENTATION
ARTIFACT, not a real property of the rule -- any node-local-budget
relaxation (V4-K1c) would then be premature and possibly irrelevant. If
the pruned set (mapped back) matches exactly, concentration is a GENUINE
property of the current rule.
"""

import sys
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import (
    HebbianAdaptation,
    StateTrajectory,
    time_averaged_correlation,
)
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import CorrelationScorer, RateBasedTopologyRule
from boyko_benchmark.experiment.runner import ADAPTATION_DTAU, localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.graphs.damage import corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.types import WeightedGraph

N_SIDE_LENGTH = 8  # N = 512
DAMAGE_FRACTION = 0.10
RHO = 0.01
M_PERSISTENCE = 3
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
MASTER_SEED = 20260818  # identical to M2/[A57]/[A58] -- SAME damaged lattices
N_SEEDS = 5
PRUNE_WINDOW = 2  # [A58]: pruning first happens at window index 2 on every seed
N_WINDOWS_TO_RUN = PRUNE_WINDOW + 1
PERMUTATION_SEED = 999

_DAMAGE_STREAM = 0
_TIEBREAK_STREAM = 1
_REGROWTH_STREAM = 2

Edge = tuple[int, int]


def edge_set(mask: NDArray[np.bool_]) -> frozenset[Edge]:
    return frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(mask)))


@dataclass(frozen=True)
class WindowRunResult:
    pre_mask: NDArray[np.bool_]
    pre_weights: NDArray[np.floating]
    pruned: frozenset[Edge]
    trajectory: StateTrajectory


def build_damaged_graph(seed_index: int) -> tuple[WeightedGraph, int, int, int]:
    seed_manager = SeedManager(MASTER_SEED)
    graph = generate_periodic_cubic_lattice(N_SIDE_LENGTH)
    coords = lattice_coordinates(N_SIDE_LENGTH)
    center_coord = np.array([N_SIDE_LENGTH // 2] * 3)
    center_index = int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))

    damage_rng = seed_manager.child_generator(seed_index, _DAMAGE_STREAM)
    damaged_graph, _damaged_out = corrupt_lattice_edges(graph, damage_rng, DAMAGE_FRACTION)

    tiebreak_seed = int(seed_manager.child_seed(seed_index, _TIEBREAK_STREAM).generate_state(1)[0])
    regrowth_seed = int(seed_manager.child_seed(seed_index, _REGROWTH_STREAM).generate_state(1)[0])
    return damaged_graph, center_index, tiebreak_seed, regrowth_seed


def run_to_prune_window(
    graph: WeightedGraph,
    source_index: int,
    tiebreak_seed: int,
    regrowth_seed: int,
) -> WindowRunResult:
    """Drives windows 0..PRUNE_WINDOW, returns the PRUNE_WINDOW's
    pre-topology-update state (mask/weights/trajectory) plus the pruned
    edge set -- everything needed for the concentration report."""
    psi0 = localized_psi0(graph.n_nodes, source_index)
    rule = RateBasedTopologyRule(
        rho=RHO,
        m=M_PERSISTENCE,
        regrow_scorer=CorrelationScorer(),
        topology_tiebreak_seed=tiebreak_seed,
        control_regrowth_seed=regrowth_seed,
    )
    adaptation_rule = HebbianAdaptation(eta=ETA)
    backend = ClosedUnitaryBackend()

    g = graph
    psi = psi0
    result: WindowRunResult | None = None
    for window_index in range(N_WINDOWS_TO_RUN):
        hamiltonian = normalized_laplacian(g)
        states = backend.evolve(hamiltonian, psi, DT, K_SUBSTEPS, 0.0, 0.0, None)
        trajectory = StateTrajectory(states=states)
        g = adaptation_rule.update(g, trajectory, ADAPTATION_DTAU)
        pre_mask = g.mask.copy()
        pre_weights = g.weights.copy()
        edges_pre = edge_set(pre_mask)
        g_after = rule.update(g, trajectory, ADAPTATION_DTAU)
        edges_after = edge_set(g_after.mask)
        pruned = edges_pre - edges_after
        if window_index == PRUNE_WINDOW:
            result = WindowRunResult(
                pre_mask=pre_mask, pre_weights=pre_weights, pruned=pruned, trajectory=trajectory
            )
        g = g_after
        psi = states[-1]

    assert result is not None
    return result


def gini(counts: NDArray[np.floating]) -> float:
    x = np.sort(counts.astype(float))
    n = len(x)
    total = x.sum()
    if total == 0:
        return 0.0
    cumx = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cumx) / total) / n)


def hhi(counts: NDArray[np.floating]) -> float:
    total = counts.sum()
    if total == 0:
        return 0.0
    shares = counts / total
    return float(np.sum(shares**2))


def report_concentration(seed_index: int, result: WindowRunResult, n_nodes: int) -> None:
    prune_counts = np.zeros(n_nodes)
    for i, j in result.pruned:
        prune_counts[i] += 1
        prune_counts[j] += 1

    histogram = np.bincount(prune_counts.astype(int), minlength=7)
    n_affected = int((prune_counts > 0).sum())
    total_prunes_incidences = prune_counts.sum()
    sorted_desc = np.sort(prune_counts)[::-1]
    top1_share = float(sorted_desc[0] / total_prunes_incidences) if total_prunes_incidences else 0.0
    top3_share = (
        float(sorted_desc[:3].sum() / total_prunes_incidences) if total_prunes_incidences else 0.0
    )
    max_node = int(np.argmax(prune_counts))
    max_node_count = int(prune_counts[max_node])

    edges_pre = edge_set(result.pre_mask)
    weight_values = np.array([result.pre_weights[i, j] for i, j in edges_pre])
    n_unique_weights = len(np.unique(weight_values))

    correlation = time_averaged_correlation(result.trajectory)
    max_node_degree = int(result.pre_mask[max_node].sum())
    max_node_strength = float(result.pre_weights[max_node].sum())
    max_node_density = float(correlation[max_node, max_node])
    max_node_neighbors = np.flatnonzero(result.pre_mask[max_node])
    max_node_mean_abs_corr = (
        float(np.mean(np.abs(correlation[max_node, max_node_neighbors])))
        if len(max_node_neighbors) > 0
        else float("nan")
    )

    print(f"\n=== seed {seed_index}, window {PRUNE_WINDOW} concentration report ===")
    print(f"histogram (n_prune=0..6+): {histogram.tolist()}")
    print(f"affected nodes: {n_affected} / {n_nodes}")
    print(f"top-1 node share of all prune-incidences: {top1_share:.3f}")
    print(f"top-3 nodes share of all prune-incidences: {top3_share:.3f}")
    print(f"Gini: {gini(prune_counts):.4f}  HHI: {hhi(prune_counts):.4f}")
    print(f"max node: {max_node} (n_prune={max_node_count})")
    print(
        f"  pre-prune degree={max_node_degree} strength={max_node_strength:.4f} "
        f"density={max_node_density:.6f} mean|corr| over its edges={max_node_mean_abs_corr:.6f}"
    )
    tie_flag = "MASSIVE TIES" if n_unique_weights < len(edges_pre) * 0.5 else "mostly distinct"
    print(
        f"distinct weight values among {len(edges_pre)} existing edges pre-prune: "
        f"{n_unique_weights} ({tie_flag})"
    )


def run_concentration_reports() -> None:
    for seed_index in range(N_SEEDS):
        graph, center_index, tiebreak_seed, regrowth_seed = build_damaged_graph(seed_index)
        result = run_to_prune_window(graph, center_index, tiebreak_seed, regrowth_seed)
        report_concentration(seed_index, result, graph.n_nodes)


def permute_graph(graph: WeightedGraph, perm: NDArray[np.intp]) -> WeightedGraph:
    """`new_graph`'s node `a` holds OLD node `perm[a]`'s identity --
    `new_mask[a,b] = old_mask[perm[a],perm[b]]`, standard permutation-
    similarity `P G P^T` via fancy indexing."""
    new_mask = graph.mask[np.ix_(perm, perm)]
    new_weights = graph.weights[np.ix_(perm, perm)]
    return WeightedGraph(mask=new_mask, weights=new_weights)


def run_equivariance_test() -> None:
    print("\n=== permutation-equivariance red-team test (seed 0) ===")
    graph, center_index, tiebreak_seed, regrowth_seed = build_damaged_graph(0)
    n_nodes = graph.n_nodes

    original_result = run_to_prune_window(graph, center_index, tiebreak_seed, regrowth_seed)
    original_pruned = original_result.pruned
    original_counts = [sum(1 for e in original_pruned if n in e) for n in range(n_nodes)]
    original_max_node = int(np.argmax(original_counts))
    print(f"original run: {len(original_pruned)} pruned edges, max node {original_max_node}")

    perm_rng = np.random.default_rng(PERMUTATION_SEED)
    perm: NDArray[np.intp] = perm_rng.permutation(n_nodes)
    inv_perm = np.argsort(perm)

    relabeled_graph = permute_graph(graph, perm)
    relabeled_center_index = int(inv_perm[center_index])

    relabeled_result = run_to_prune_window(
        relabeled_graph, relabeled_center_index, tiebreak_seed, regrowth_seed
    )
    relabeled_pruned = relabeled_result.pruned

    # Map the relabeled run's pruned edges back to ORIGINAL labels:
    # relabeled node a's identity is perm[a] (see permute_graph's docstring).
    mapped_back_pruned = frozenset(
        (int(min(perm[i], perm[j])), int(max(perm[i], perm[j]))) for i, j in relabeled_pruned
    )

    print(f"relabeled run: {len(relabeled_pruned)} pruned edges (in new labels)")
    print(f"relabeled pruned, mapped back to original labels: {sorted(mapped_back_pruned)}")
    print(f"original pruned edges:                            {sorted(original_pruned)}")

    matches = mapped_back_pruned == original_pruned
    overlap = len(mapped_back_pruned & original_pruned)
    print(f"\nExact match after mapping back: {matches}")
    print(
        f"Overlap: {overlap}/{len(original_pruned)} original pruned edges also pruned "
        f"(after relabeling+mapping back)"
    )
    if matches:
        print(
            "VERDICT: GENUINE -- pruning selection is permutation-equivariant. "
            "Concentration is a real property of the rule, not a labeling artifact."
        )
    else:
        print(
            "VERDICT: ARTIFACT -- relabeling changed WHICH physical edges got pruned. "
            "Tie-break/ordering leak suspected -- do NOT pre-register V4-K1c yet."
        )


def main() -> int:
    print("=== K1 concentration + permutation-equivariance audit ===")
    print(
        f"N={N_SIDE_LENGTH**3}, rho={RHO}, m={M_PERSISTENCE}, damage={DAMAGE_FRACTION}, "
        f"eta={ETA}, master_seed={MASTER_SEED}, prune_window={PRUNE_WINDOW}"
    )
    run_concentration_reports()
    run_equivariance_test()
    return 0


if __name__ == "__main__":
    sys.exit(main())
