"""M2 (`docs/v4_spec.md` Sec7, K1 gate): `corrupt_lattice_edges` --
rewires a target fraction of a lattice's edges via the existing
degree-preserving `scramble_preserving_degree_sequence` (reused, not
reimplemented -- same double_edge_swap machinery Arm D already uses),
and additionally returns exactly which lattice edges were removed
(`E_damaged_out`), which K1's `R_edge` needs and the existing scramble
utility does not expose.

Hand-derived fixture (prototype run, `.venv/Scripts/python.exe`, before
any assertion was written): 6-node ring, `n_swaps=1`, `rng=default_
rng(3)` deterministically removes edges (0,1) and (2,3), introduces
(0,2) and (1,3). Verified by direct inspection of `scramble_preserving_
degree_sequence`'s output, not assumed.
"""

import numpy as np

from boyko_benchmark.graphs.damage import corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, generate_periodic_ring


def test_corrupt_lattice_edges_matches_hand_derived_ring_example() -> None:
    graph = generate_periodic_ring(n_nodes=6)
    rng = np.random.default_rng(3)

    damaged, damaged_out = corrupt_lattice_edges(graph, rng, fraction=1 / 3)

    assert damaged_out == frozenset({(0, 1), (2, 3)})
    new_edges = set(map(tuple, np.argwhere(np.triu(damaged.mask))))
    assert (0, 2) in new_edges
    assert (1, 3) in new_edges
    assert (0, 1) not in new_edges
    assert (2, 3) not in new_edges


def test_corrupt_lattice_edges_preserves_edge_count() -> None:
    graph = generate_periodic_ring(n_nodes=6)
    rng = np.random.default_rng(3)
    n_before = int(graph.mask.sum())

    damaged, _ = corrupt_lattice_edges(graph, rng, fraction=1 / 3)

    assert int(damaged.mask.sum()) == n_before


def test_damaged_out_is_subset_of_original_edges() -> None:
    graph = generate_periodic_cubic_lattice(side_length=8)
    rng = np.random.default_rng(11)
    original_edges = frozenset(map(tuple, np.argwhere(np.triu(graph.mask))))

    _, damaged_out = corrupt_lattice_edges(graph, rng, fraction=0.10)

    assert damaged_out.issubset(original_edges)
    assert len(damaged_out) > 0


def test_corrupt_lattice_edges_hits_approximately_the_requested_fraction() -> None:
    """[WEAK, documented not asserted-precise]: double_edge_swap can fail
    a subset of individual swap attempts (duplicate/self-loop rejection
    internal to networkx), so the realized fraction is a close
    approximation, not exact -- verified via prototype at N=512 (target
    154, actual 146, `docs/v4_spec.md` Sec7's own 10% is a design target,
    not a promised exact count)."""
    graph = generate_periodic_cubic_lattice(side_length=8)
    rng = np.random.default_rng(11)
    n_edges = int(graph.mask.sum()) // 2

    _, damaged_out = corrupt_lattice_edges(graph, rng, fraction=0.10)

    target = round(0.10 * n_edges)
    assert target * 0.8 <= len(damaged_out) <= target
