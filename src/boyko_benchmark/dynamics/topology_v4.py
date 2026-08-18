"""V4 (`docs/v4_spec.md`, `mathematical_contract.md` Sec3.3 Addendum 3):
`StatefulTopologyRule` -- the first topology rule in this project
permitted to ADD an edge, scoped explicitly to V4's own arms (never a
replacement for any Stage-1 arm's `NoTopologyUpdate`).

Persistence-counter semantics, hand-verified before any test was written
(prototype: 4-node ring, edge (2,3) permanently lowest-weight, rho=0.25,
m=2):

    window 0: low_set={(2,3)}  persistence={(2,3): 1}  eligible=[]
    window 1: low_set={(2,3)}  persistence={(2,3): 2}  eligible=[(2,3)]

An edge's counter increments only while it stays in the bottom-rho
quantile on EVERY consecutive window; leaving the low set even once
resets it to 0 (`docs/v4_spec.md` Sec4's "sustained low utility, not a
coin flip").
"""

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import StateTrajectory, time_averaged_correlation
from boyko_benchmark.observables.propagation_front import hop_distances_from_source
from boyko_benchmark.types import WeightedGraph

Edge = tuple[int, int]

NEW_EDGE_WEIGHT = 1.0
"""[A19]'s uniform-initial-weight convention, extended to regrown edges
-- a newly created edge starts exactly where every edge started."""


def graph_distance_matrix(mask: NDArray[np.bool_]) -> NDArray[np.int64]:
    """All-pairs unweighted hop distance, built from `hop_distances_from_
    source` (reused, not reimplemented) called once per node. O(N) BFS
    calls, each O(N+E) -- O(N^2) total at this project's graph sizes,
    negligible next to the propagation step."""
    n_nodes = mask.shape[0]
    distances = np.zeros((n_nodes, n_nodes), dtype=np.int64)
    for source in range(n_nodes):
        distances[source] = hop_distances_from_source(mask, source)
    return distances


class RegrowScorer(Protocol):
    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        candidates: list[Edge],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]: ...


class UniformRandomScorer:
    """Arm A2 (`docs/v4_spec.md` Sec4): i.i.d. random scores, ignoring
    both correlation and distance entirely -- the naive/diagnostic
    baseline (`Delta_naive`)."""

    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        candidates: list[Edge],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]:
        return rng.random(len(candidates))


class CorrelationScorer:
    """Arm A3 (`docs/v4_spec.md` Sec4, Sec12): the real time-averaged
    correlation `C_ij` for each candidate pair -- deterministic Top-K is
    applied to this by `RateBasedTopologyRule`, not here."""

    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        candidates: list[Edge],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]:
        correlation = time_averaged_correlation(trajectory)
        return np.array([correlation[i, j] for i, j in candidates])


class DistanceStratifiedShuffleScorer:
    """Arm A4 (`docs/v4_spec.md` Sec5, Revision 1): permutes a base
    scorer's real values ONLY within graph-distance strata -- preserves
    the event count, the value multiset, and the empirical distance-vs-
    correlation dependence; destroys only which specific pair at a given
    distance receives which value. `Delta_specific`'s control arm.
    """

    def __init__(self, base_scorer: RegrowScorer, distance_bins: tuple[int, ...] = (2, 3)) -> None:
        self._base_scorer = base_scorer
        self._distance_bins = distance_bins

    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        candidates: list[Edge],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]:
        real_scores = self._base_scorer.score(graph, trajectory, candidates, rng)
        distances = graph_distance_matrix(graph.mask)
        candidate_distances = np.array([distances[i, j] for i, j in candidates])
        stratum_of = np.array(
            [self._stratum(d) for d in candidate_distances],
        )

        shuffled = real_scores.copy()
        for stratum in np.unique(stratum_of):
            idx = np.flatnonzero(stratum_of == stratum)
            if len(idx) > 1:
                permuted_idx = rng.permutation(idx)
                shuffled[idx] = real_scores[permuted_idx]
        return shuffled

    def _stratum(self, distance: int) -> int:
        for edge_bin in self._distance_bins:
            if distance <= edge_bin:
                return edge_bin
        return self._distance_bins[-1] + 1  # catch-all "far" stratum


class StatefulTopologyRule(Protocol):
    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph: ...


class RateBasedTopologyRule:
    """`docs/v4_spec.md` Sec4: prune the persistently-lowest-weight
    `rho*|E|` edges (eligible only after `m` consecutive windows in the
    bottom-rho quantile), regrow exactly as many via `regrow_scorer`'s
    deterministic Top-K. Never adds an edge as a side effect -- only via
    this explicit, declared selection rule (`mathematical_contract.md`
    Sec3.3 Addendum 3).

    Carries persistent per-edge state (`persistence_counters`) across
    `update` calls -- this is what makes topology "an independent state
    variable with memory" rather than a pure function of the current
    window's weights.
    """

    def __init__(self, rho: float, m: int, regrow_scorer: RegrowScorer, rng_seed: int) -> None:
        self._rho = rho
        self._m = m
        self._regrow_scorer = regrow_scorer
        self._rng = np.random.default_rng(rng_seed)
        self.persistence_counters: dict[frozenset[int], int] = {}

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        existing_edges = [(int(i), int(j)) for i, j in np.argwhere(np.triu(graph.mask))]
        n_edges = len(existing_edges)
        n_target = max(1, round(self._rho * n_edges)) if n_edges > 0 else 0

        low_set = sorted(existing_edges, key=lambda e: graph.weights[e[0], e[1]])[:n_target]
        low_set_keys = {frozenset(e) for e in low_set}

        for edge in existing_edges:
            key = frozenset(edge)
            if key in low_set_keys:
                self.persistence_counters[key] = self.persistence_counters.get(key, 0) + 1
            else:
                self.persistence_counters.pop(key, None)

        eligible = [e for e in low_set if self.persistence_counters.get(frozenset(e), 0) >= self._m]
        eligible.sort(
            key=lambda e: (
                -self.persistence_counters[frozenset(e)],
                graph.weights[e[0], e[1]],
            )
        )
        n_to_prune = min(n_target, len(eligible))
        to_prune = eligible[:n_to_prune]

        if n_to_prune == 0:
            return graph

        candidates = [
            (i, j)
            for i in range(graph.n_nodes)
            for j in range(i + 1, graph.n_nodes)
            if not graph.mask[i, j]
        ]
        scores = self._regrow_scorer.score(graph, trajectory, candidates, self._rng)
        order = np.argsort(-scores, kind="stable")  # deterministic Top-K, stable tie-break
        to_regrow = [candidates[k] for k in order[:n_to_prune]]

        new_mask = graph.mask.copy()
        new_weights = graph.weights.copy()
        for i, j in to_prune:
            new_mask[i, j] = new_mask[j, i] = False
            new_weights[i, j] = new_weights[j, i] = 0.0
            self.persistence_counters.pop(frozenset((i, j)), None)
        for i, j in to_regrow:
            new_mask[i, j] = new_mask[j, i] = True
            new_weights[i, j] = new_weights[j, i] = NEW_EDGE_WEIGHT

        return WeightedGraph(mask=new_mask, weights=new_weights)
