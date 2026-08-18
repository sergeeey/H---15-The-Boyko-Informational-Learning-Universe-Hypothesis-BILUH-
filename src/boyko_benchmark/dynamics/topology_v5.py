"""V5 (`docs/v5_spec.md`, `mathematical_contract.md` Addendum 5):
degree-preserving connected edge swap -- the elementary structural
operation replacing V4's independent edge deletion, following
`docs/assumptions.md` `[A64]`'s diagnosis that independent deletion,
decoupled from creation, is what manufactures star-collapse. A swap
`(a,b),(c,d) -> (a,c),(b,d)` (or `(a,d),(b,c)`) leaves every node's
degree exactly unchanged -- there is no incidence cap here because the
failure mode it would guard against cannot arise from this operation.

**Performance note, found while implementing M1, not assumed:** at
N=512 (T7/`[A32]`'s lattice, 1536 edges), there are ~2.3 million
node-disjoint edge-pair candidates. A naive Python-object-per-candidate
implementation took 6.3s to ENUMERATE alone (measured,
`.venv/Scripts/python.exe -c "..."`), and constructing that many
`SwapCandidate` dataclass instances added ~2.8s more -- at K1'-scale
swap budgets (~15 swaps/window x 50 windows x 5 seeds x 2 arms = 7500
calls), a naive approach would take multiple HOURS. `generate_swap_
candidates` therefore returns NumPy arrays, not a list of dataclasses,
and scorers operate on those arrays directly; `SwapCandidate` objects
are constructed only for the handful of top-ranked candidates actually
tried for connectivity legality (typically just one per swap slot).
Vectorized enumeration alone measured at 0.14s for the same graph --
see `docs/assumptions.md` for the dated performance finding.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import StateTrajectory, time_averaged_correlation
from boyko_benchmark.dynamics.topology_v4 import NEW_EDGE_WEIGHT, graph_distance_matrix
from boyko_benchmark.observables.propagation_front import hop_distances_from_source
from boyko_benchmark.types import WeightedGraph

Edge = tuple[int, int]


@dataclass(frozen=True)
class SwapCandidate:
    remove: tuple[Edge, Edge]
    add: tuple[Edge, Edge]


def generate_swap_candidates(
    mask: NDArray[np.bool_],
) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    """Vectorized enumeration of all node-disjoint existing-edge pairs,
    both reconnections, filtered to exclude multi-edges. Returns
    `(remove, add)`, each shape `(K, 2, 2)`: `remove[k] = [[a,b],[c,d]]`
    (the two edges deleted), `add[k] = [[e1i,e1j],[e2i,e2j]]` (the two
    edges created), each inner pair already sorted `(min, max)`.
    Connectivity is deliberately NOT checked here -- checked lazily in
    `BalancedSwapTopologyRule`, only for candidates actually considered
    during selection (`docs/v5_spec.md` Sec4)."""
    edges = np.argwhere(np.triu(mask))
    n = len(edges)
    if n < 2:
        empty = np.empty((0, 2, 2), dtype=np.int64)
        return empty, empty

    idx_i, idx_j = np.triu_indices(n, k=1)
    a, b = edges[idx_i, 0], edges[idx_i, 1]
    c, d = edges[idx_j, 0], edges[idx_j, 1]
    disjoint = (a != c) & (a != d) & (b != c) & (b != d)
    a, b, c, d = a[disjoint], b[disjoint], c[disjoint], d[disjoint]

    remove_parts = []
    add_parts = []
    for p, q, r, s in ((a, c, b, d), (a, d, b, c)):
        edge1 = np.stack([np.minimum(p, q), np.maximum(p, q)], axis=1)
        edge2 = np.stack([np.minimum(r, s), np.maximum(r, s)], axis=1)
        legal = ~mask[edge1[:, 0], edge1[:, 1]] & ~mask[edge2[:, 0], edge2[:, 1]]
        remove_pair = np.stack([np.stack([a, b], axis=1), np.stack([c, d], axis=1)], axis=1)
        add_pair = np.stack([edge1, edge2], axis=1)
        remove_parts.append(remove_pair[legal])
        add_parts.append(add_pair[legal])

    remove = np.concatenate(remove_parts, axis=0)
    add = np.concatenate(add_parts, axis=0)
    return remove, add


def apply_swap(graph: WeightedGraph, swap: SwapCandidate, new_edge_weight: float) -> WeightedGraph:
    """Removes `swap.remove`, adds `swap.add` at `new_edge_weight` --
    every other edge's weight is untouched, matching V4's own
    established convention that only the edges actually changed by a
    topology operation have their weight touched."""
    new_mask = graph.mask.copy()
    new_weights = graph.weights.copy()
    for i, j in swap.remove:
        new_mask[i, j] = new_mask[j, i] = False
        new_weights[i, j] = new_weights[j, i] = 0.0
    for i, j in swap.add:
        new_mask[i, j] = new_mask[j, i] = True
        new_weights[i, j] = new_weights[j, i] = new_edge_weight
    return WeightedGraph(mask=new_mask, weights=new_weights)


def _is_connected(mask: NDArray[np.bool_]) -> bool:
    return bool(np.all(hop_distances_from_source(mask, 0) != -1))


class SwapScorer(Protocol):
    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        remove: NDArray[np.int64],
        add: NDArray[np.int64],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]: ...


class CorrelationSwapScorer:
    """Arm A3 (`docs/v5_spec.md` Sec4/Sec5): `Delta_S = C_added -
    C_removed`, using the same time-averaged correlation V4 used.
    Vectorized: one array lookup per side, not a Python loop."""

    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        remove: NDArray[np.int64],
        add: NDArray[np.int64],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]:
        correlation = time_averaged_correlation(trajectory)
        c_removed = (
            correlation[remove[:, 0, 0], remove[:, 0, 1]]
            + correlation[remove[:, 1, 0], remove[:, 1, 1]]
        )
        c_added = correlation[add[:, 0, 0], add[:, 0, 1]] + correlation[add[:, 1, 0], add[:, 1, 1]]
        result: NDArray[np.floating] = c_added - c_removed
        return result


class DistanceStratifiedSwapScorer:
    """Arm A4 (`docs/v5_spec.md` Sec4/Sec6): permutes a base scorer's
    real `Delta_S` values only within strata of the MIN pre-swap graph
    distance between the two NEW edges' endpoints a candidate would
    create -- same "preserve the value multiset and distance
    dependence, destroy only pair-specific correspondence" principle as
    V4's own `DistanceStratifiedShuffleScorer`, adapted to a
    2-edge-per-candidate shape (a swap candidate has no single
    well-defined "distance" the way a single regrow candidate did)."""

    def __init__(self, base_scorer: SwapScorer, distance_bins: tuple[int, ...] = (2, 3)) -> None:
        self._base_scorer = base_scorer
        self._distance_bins = distance_bins

    def score(
        self,
        graph: WeightedGraph,
        trajectory: StateTrajectory,
        remove: NDArray[np.int64],
        add: NDArray[np.int64],
        rng: np.random.Generator,
    ) -> NDArray[np.floating]:
        real_scores = self._base_scorer.score(graph, trajectory, remove, add, rng)
        distances = graph_distance_matrix(graph.mask)
        dist1 = distances[add[:, 0, 0], add[:, 0, 1]]
        dist2 = distances[add[:, 1, 0], add[:, 1, 1]]
        candidate_min_distance = np.minimum(dist1, dist2)
        if np.any(candidate_min_distance < 0):
            raise ValueError(
                "DistanceStratifiedSwapScorer: a candidate's new edge spans an "
                "unreachable (hop distance -1) pair -- V5's population is restricted "
                "to graphs that stay connected by construction (docs/v5_spec.md Sec3); "
                "this indicates a precondition violation upstream, not handled here."
            )
        stratum_of = np.array([self._stratum(int(d)) for d in candidate_min_distance])

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
        return self._distance_bins[-1] + 1


class BalancedSwapTopologyRule:
    """V5 (`docs/v5_spec.md` Sec4, Sec8 M1): commits `n_swaps` per
    window, each a deterministic argmax (seeded tiebreak) over
    structurally-legal candidates, walked in ranked order until a
    CONNECTIVITY-legal one is found (or the ranked list is exhausted,
    in which case that swap slot is skipped -- `docs/v5_spec.md` Sec7's
    `K_skip`). No incidence cap: degree is invariant under this
    operation by construction, so there is nothing to cap.

    `SwapCandidate` objects are constructed only for indices actually
    walked during the connectivity-legality search, not for the full
    (potentially millions-large) candidate pool -- see this module's
    top-level performance note.

    `last_committed`/`last_skipped_count` are exposed publicly (same
    style as V4's `last_pruned`/`last_eligible`) for `K_skip` reporting.
    """

    def __init__(
        self,
        n_swaps: int,
        score_scorer: SwapScorer,
        tiebreak_seed: int,
        control_seed: int,
    ) -> None:
        self._n_swaps = n_swaps
        self._scorer = score_scorer
        self._tiebreak_rng = np.random.default_rng(tiebreak_seed)
        self._control_rng = np.random.default_rng(control_seed)
        self.last_committed: tuple[SwapCandidate, ...] = ()
        self.last_skipped_count = 0

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        current = graph
        committed: list[SwapCandidate] = []
        skipped = 0

        for _ in range(self._n_swaps):
            remove, add = generate_swap_candidates(current.mask)
            if len(remove) == 0:
                skipped += 1
                continue

            scores = self._scorer.score(current, trajectory, remove, add, self._control_rng)
            tiebreak = self._tiebreak_rng.random(len(remove))
            order = np.lexsort((tiebreak, -scores))

            committed_this_slot = False
            for idx in order:
                candidate = SwapCandidate(
                    remove=(
                        (int(remove[idx, 0, 0]), int(remove[idx, 0, 1])),
                        (int(remove[idx, 1, 0]), int(remove[idx, 1, 1])),
                    ),
                    add=(
                        (int(add[idx, 0, 0]), int(add[idx, 0, 1])),
                        (int(add[idx, 1, 0]), int(add[idx, 1, 1])),
                    ),
                )
                proposed = apply_swap(current, candidate, NEW_EDGE_WEIGHT)
                if _is_connected(proposed.mask):
                    current = proposed
                    committed.append(candidate)
                    committed_this_slot = True
                    break
            if not committed_this_slot:
                skipped += 1

        self.last_committed = tuple(committed)
        self.last_skipped_count = skipped
        return current
