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

import math
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
        if np.any(candidate_distances < 0):
            # WHY: hop_distances_from_source's own convention (-1 for
            # unreachable) must be raised at the point of consumption,
            # matching observables/propagation_front.py's identical
            # pattern for the same value -- silently folding -1 into
            # the nearest real stratum would misclassify a disconnected
            # pair as distance-2 (review finding: -1 <= 2 is True).
            raise ValueError(
                "DistanceStratifiedShuffleScorer: candidate pair is unreachable/disconnected "
                "(hop distance -1) -- the topology's population is restricted to connected "
                "graphs (docs/v4_spec.md Sec3's while-active ICE strategy handles this at the "
                "run-loop level, not here)."
            )
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

    def __init__(
        self,
        rho: float,
        m: int,
        regrow_scorer: RegrowScorer,
        topology_tiebreak_seed: int,
        control_regrowth_seed: int,
    ) -> None:
        """Two independent seed streams (`docs/v4_spec.md` Sec3's six-
        stream discipline, scoped to what this class owns):
        `topology_tiebreak_seed` breaks exact numerical ties in the
        deterministic Top-K regrow selection ONLY (`[A11]`-style
        independence from the scoring randomness itself); `control_
        regrowth_seed` drives the scorer's own randomness (A2's uniform
        draw, A4's within-stratum shuffle -- a no-op for A3's
        `CorrelationScorer`, which ignores its `rng` argument). Funnelling
        both through one seed would let the two draws' sequences drift
        against each other the moment one consumes the stream a
        different number of times than the other, exactly the failure
        mode Sec3 names."""
        self._rho = rho
        self._m = m
        self._regrow_scorer = regrow_scorer
        self._tiebreak_rng = np.random.default_rng(topology_tiebreak_seed)
        self._regrow_rng = np.random.default_rng(control_regrowth_seed)
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

        # WHY no ranking/truncation here: `eligible` is by construction a
        # subset of `low_set` (size <= n_target), so every eligible edge
        # is always pruned in full -- there is never an oversupply to
        # rank among. An earlier version sorted+capped this as if there
        # could be, which was dead code (review finding 3).
        eligible = [e for e in low_set if self.persistence_counters.get(frozenset(e), 0) >= self._m]
        to_prune = eligible
        n_to_prune = len(to_prune)

        if n_to_prune == 0:
            return graph

        candidates = [
            (i, j)
            for i in range(graph.n_nodes)
            for j in range(i + 1, graph.n_nodes)
            if not graph.mask[i, j]
        ]
        if len(candidates) < n_to_prune:
            # WHY: at this project's real budgets (N=512, mean degree 6,
            # ~129k non-edges vs ~15 pruned/window) this cannot occur --
            # asserted rather than silently letting the edge-budget
            # invariant (|E| constant, central to A3-vs-A4 comparability)
            # break with no error (review finding 4).
            raise ValueError(
                f"RateBasedTopologyRule: only {len(candidates)} regrow candidates available "
                f"for {n_to_prune} pruned edges -- graph is too dense for this rho."
            )
        scores = self._regrow_scorer.score(graph, trajectory, candidates, self._regrow_rng)
        # WHY: deterministic Top-K primary-sorted by score; exact ties
        # broken by an independent seeded stream (topology_tiebreak_seed),
        # not by candidate list position -- np.lexsort sorts by the LAST
        # key first, so (-scores) is primary and tiebreak is secondary.
        tiebreak = self._tiebreak_rng.random(len(candidates))
        order = np.lexsort((tiebreak, -scores))
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


def bounded_incidence_cap(degree: int, q: float, d_min: int = 1) -> int:
    """V4-K1c (`docs/v4_spec.md` Sec7d, Revision 2): `b_i = max(0,
    min(floor(q*d_i), d_i - d_min))` -- how many of a node's CURRENT
    `degree` edges the prune step may remove in one window.

    NOT `max(1, floor(q*d))` (the naive form, and the spec's own
    documented rejection of it): at `degree=1`, `floor(q*1)=0` already,
    but a `max(1, ...)` floor would force `b=1`, allowing a node's LAST
    edge to be pruned -- re-introducing the exact single-window full-
    isolation failure this relaxation exists to prevent. The `d_i-d_min`
    term instead caps the cap itself, so a node is never allowed to drop
    below `d_min` surviving edges via this mechanism, for ANY starting
    degree.
    """
    return max(0, min(math.floor(q * degree), degree - d_min))


class BoundedIncidenceTopologyRule:
    """V4-K1c (`docs/v4_spec.md` Sec7d, Revision 2, pre-registered
    2026-08-18): identical persistence-gated, weight-sorted pruning to
    `RateBasedTopologyRule`, except the final selection of WHICH
    persistence-eligible edges actually get pruned this window is a
    constrained (capacitated) selection -- `bounded_incidence_cap`
    limits how many of any single node's CURRENT edges may be pruned in
    one window, so a single window can no longer remove 100% of a
    node's incident edges the way `[A57]`-`[A59]` found `RateBased
    TopologyRule` reproducibly does.

    Implemented as a deterministic greedy walk (score-descending =
    weight-ascending, fixed ordering) over the eligible set, adding an
    edge to the prune selection only while neither endpoint's cap is
    yet exhausted -- an accepted PRACTICAL approximation to the
    formally-stated constrained selection problem (`docs/v4_spec.md`
    Sec7d), not claimed to be the exact combinatorial optimum.

    Regrowth is sized to the ACTUAL prune count (which may be smaller
    than `n_target` when caps bind), not the target -- preserves the
    edge-budget-conservation invariant. Regrowth itself is NOT capped
    (Sec7d: concentration there is logged, not pre-emptively fixed).

    `last_eligible`/`last_pruned`/`last_regrown` are exposed publicly
    (same style as `persistence_counters`) so a caller can compute
    Sec7d's ICE-1 (exposure) and ICE-3 (cap activity) diagnostics
    externally, without duplicating selection logic.
    """

    def __init__(
        self,
        rho: float,
        m: int,
        q: float,
        regrow_scorer: RegrowScorer,
        topology_tiebreak_seed: int,
        control_regrowth_seed: int,
        d_min: int = 1,
    ) -> None:
        self._rho = rho
        self._m = m
        self._q = q
        self._d_min = d_min
        self._regrow_scorer = regrow_scorer
        self._tiebreak_rng = np.random.default_rng(topology_tiebreak_seed)
        self._regrow_rng = np.random.default_rng(control_regrowth_seed)
        self.persistence_counters: dict[frozenset[int], int] = {}
        self.last_eligible: frozenset[Edge] = frozenset()
        self.last_pruned: frozenset[Edge] = frozenset()
        self.last_regrown: frozenset[Edge] = frozenset()

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
        self.last_eligible = frozenset(eligible)

        if not eligible:
            self.last_pruned = frozenset()
            self.last_regrown = frozenset()
            return graph

        # WHY: score-descending = weight-ascending (lowest weight is
        # most prune-desirable), same direction as RateBasedTopologyRule
        # -- fixed, reproducible ordering for the greedy walk.
        eligible_sorted = sorted(eligible, key=lambda e: graph.weights[e[0], e[1]])

        current_degree = {
            node: int(graph.mask[node].sum()) for node in {n for e in eligible_sorted for n in e}
        }
        caps = {
            node: bounded_incidence_cap(degree, self._q, self._d_min)
            for node, degree in current_degree.items()
        }
        selected_count: dict[int, int] = dict.fromkeys(caps, 0)

        to_prune: list[Edge] = []
        for i, j in eligible_sorted:
            # WHY this break is dead code, same as RateBasedTopologyRule's
            # analogous comment: eligible is always a subset of low_set
            # (size <= n_target), so len(to_prune) can never reach
            # n_target before eligible_sorted itself is exhausted. Kept
            # as an explicit invariant guard, not because it's reachable.
            if len(to_prune) >= n_target:
                break
            if selected_count[i] < caps[i] and selected_count[j] < caps[j]:
                to_prune.append((i, j))
                selected_count[i] += 1
                selected_count[j] += 1

        n_to_prune = len(to_prune)
        self.last_pruned = frozenset(to_prune)

        if n_to_prune == 0:
            self.last_regrown = frozenset()
            return graph

        candidates = [
            (i, j)
            for i in range(graph.n_nodes)
            for j in range(i + 1, graph.n_nodes)
            if not graph.mask[i, j]
        ]
        if len(candidates) < n_to_prune:
            raise ValueError(
                f"BoundedIncidenceTopologyRule: only {len(candidates)} regrow candidates "
                f"available for {n_to_prune} pruned edges -- graph is too dense for this rho."
            )
        scores = self._regrow_scorer.score(graph, trajectory, candidates, self._regrow_rng)
        tiebreak = self._tiebreak_rng.random(len(candidates))
        order = np.lexsort((tiebreak, -scores))
        to_regrow = [candidates[k] for k in order[:n_to_prune]]
        self.last_regrown = frozenset(to_regrow)

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
