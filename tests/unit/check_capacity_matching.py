"""`max_capacity_cardinality` (`observables/capacity_matching.py`):
exact solver for `M* = max |S|, S subset of eligible_edges, s.t.
deg_S(i) <= caps[i]` -- the degree-constrained-subgraph / b-matching
problem `[A61]`/`[A63]` (`docs/assumptions.md`) use to distinguish
algorithmic weakness from structural incompatibility in V4-K1c/K1d's
exposure failures.

Reviewer-flagged gap (2026-08-18, `feat/v4-k1d-reference-degree-cap`):
the "sanity-checked on a hand-worked triangle example" claim in the
original capacity-audit scripts' docstrings had no committed test
locking it in -- this file is that test, plus an asymmetric-cap case
and the empty-input edge case.
"""

from boyko_benchmark.observables.capacity_matching import max_capacity_cardinality


def test_triangle_with_uniform_cap_one_gives_max_matching_of_one() -> None:
    """Hand-derived: a triangle (0,1),(0,2),(1,2), b_i=1 for all 3 nodes
    -- this is exactly a max-matching problem (no node can have 2
    selected edges), and a triangle's max matching size is 1 (any two
    edges share a node). M* must be 1, not 2 or 3."""
    edges = frozenset({(0, 1), (0, 2), (1, 2)})
    caps = {0: 1, 1: 1, 2: 1}

    assert max_capacity_cardinality(edges, caps) == 1


def test_triangle_with_uniform_cap_two_allows_all_three_edges() -> None:
    """Same triangle, b_i=2 for all 3 nodes -- every node can absorb
    both its incident edges, so all 3 edges are simultaneously
    selectable (each node ends up with selected-degree exactly 2)."""
    edges = frozenset({(0, 1), (0, 2), (1, 2)})
    caps = {0: 2, 1: 2, 2: 2}

    assert max_capacity_cardinality(edges, caps) == 3


def test_asymmetric_caps_hub_and_spoke() -> None:
    """Hand-derived: node 0 connects to 1,2,3 (b_0=2, can only keep 2 of
    its 3 edges); nodes 1,2,3 each have b=1 and touch only their own
    spoke to 0 (never binding). M* = 2 (limited by node 0's cap alone,
    any 2 of the 3 spokes)."""
    edges = frozenset({(0, 1), (0, 2), (0, 3)})
    caps = {0: 2, 1: 1, 2: 1, 3: 1}

    assert max_capacity_cardinality(edges, caps) == 2


def test_empty_eligible_set_gives_zero_without_calling_the_solver() -> None:
    assert max_capacity_cardinality(frozenset(), {}) == 0
