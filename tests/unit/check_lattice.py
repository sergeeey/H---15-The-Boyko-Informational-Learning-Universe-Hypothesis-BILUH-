"""Unit tests for the periodic cubic lattice generator (Arm E)."""

import numpy as np

from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.types import WeightedGraph


def test_lattice_has_correct_node_count() -> None:
    lattice = generate_periodic_cubic_lattice(side_length=3)

    assert lattice.n_nodes == 27


def test_lattice_every_node_has_degree_six() -> None:
    """side_length=3 avoids the L=2 wraparound-collision degenerate case."""
    lattice = generate_periodic_cubic_lattice(side_length=3)

    degrees = lattice.mask.sum(axis=1)
    assert np.all(degrees == 6)


def test_lattice_is_valid_weighted_graph() -> None:
    lattice = generate_periodic_cubic_lattice(side_length=3)

    assert isinstance(lattice, WeightedGraph)
    np.testing.assert_array_equal(lattice.mask, lattice.mask.T)
    assert not np.any(np.diagonal(lattice.mask))


def test_lattice_uses_uniform_initial_weight() -> None:
    lattice = generate_periodic_cubic_lattice(side_length=3)

    edge_weights = lattice.weights[lattice.mask]
    assert np.all(edge_weights == edge_weights[0])
    assert edge_weights[0] > 0


def test_lattice_periodic_boundary_wraps_around() -> None:
    """Node (0,0,0) and node (2,0,0) are adjacent via wraparound on a
    side_length=3 lattice (2+1=3 mod 3=0)."""
    lattice = generate_periodic_cubic_lattice(side_length=3)

    def index(x: int, y: int, z: int) -> int:
        return x * 9 + y * 3 + z

    assert lattice.mask[index(0, 0, 0), index(2, 0, 0)]


def test_lattice_coordinates_match_node_count() -> None:
    coords = lattice_coordinates(side_length=3)

    assert coords.shape == (27, 3)
    assert coords[:, 0].max() == 2
    assert coords[:, 0].min() == 0
