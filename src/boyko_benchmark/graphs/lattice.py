"""Periodic lattice generators.

3D is Arm E (Fixed Flat Geometry, mathematical_contract.md Sec4):
"periodic regular lattice (positive geometric calibration; never an
optimization target)". N = L^3, matching the FSS grid convention
(mathematical_contract.md Sec6). Never used as an AdaptationRule target --
Arm E always runs NoAdaptation.

1D (ring) and 2D are calibration-only graphs, not one of the seven arms --
ТЗ.txt Sec13's Milestone-1 test list names calibration targets
d_s~1 (ring), d_s~2 (square lattice), d_s~3 (cubic lattice) explicitly.
"""

from itertools import product

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.graphs.generators import INITIAL_EDGE_WEIGHT
from boyko_benchmark.types import WeightedGraph


def _generate_periodic_lattice(side_length: int, dimension: int) -> WeightedGraph:
    """Generic D-dimensional periodic (toroidal) hypercubic lattice,
    side_length^dimension nodes, each connected to its 2*dimension nearest
    neighbors under periodic boundary conditions.

    Note: side_length == 2 is a degenerate case in any dimension where the
    +1 and -1 neighbor along an axis coincide (wraparound collision),
    halving the degree for that specific size -- a well-known small-N
    periodic-lattice artifact, not a bug; side_length >= 3 does not have
    this issue.
    """
    length = side_length
    n_nodes = length**dimension
    mask = np.zeros((n_nodes, n_nodes), dtype=bool)
    weights = np.zeros((n_nodes, n_nodes), dtype=float)

    strides = [length ** (dimension - 1 - d) for d in range(dimension)]

    def index(coord: tuple[int, ...]) -> int:
        return sum((c % length) * s for c, s in zip(coord, strides, strict=True))

    for coord in product(range(length), repeat=dimension):
        i = index(coord)
        for axis in range(dimension):
            neighbor = list(coord)
            neighbor[axis] += 1
            j = index(tuple(neighbor))
            mask[i, j] = mask[j, i] = True
            weights[i, j] = weights[j, i] = INITIAL_EDGE_WEIGHT

    return WeightedGraph(mask=mask, weights=weights)


def generate_periodic_ring(n_nodes: int) -> WeightedGraph:
    """1D periodic lattice (ring). Calibration target: d_s ~ 1."""
    return _generate_periodic_lattice(side_length=n_nodes, dimension=1)


def generate_periodic_square_lattice(side_length: int) -> WeightedGraph:
    """2D periodic lattice, side_length^2 nodes. Calibration target: d_s ~ 2."""
    return _generate_periodic_lattice(side_length=side_length, dimension=2)


def generate_periodic_cubic_lattice(side_length: int) -> WeightedGraph:
    """3D periodic lattice, side_length^3 nodes (Arm E). Calibration
    target: d_s ~ 3."""
    return _generate_periodic_lattice(side_length=side_length, dimension=3)


def lattice_coordinates(side_length: int) -> NDArray[np.intp]:
    """(x, y, z) coordinates for each node index, in the same index()
    convention generate_periodic_cubic_lattice uses -- for choosing a
    geometrically-central source node ([A6]/[A17] convention note in
    mathematical_contract.md Sec2)."""
    length = side_length
    coords = np.empty((length**3, 3), dtype=np.intp)
    for x in range(length):
        for y in range(length):
            for z in range(length):
                idx = x * length * length + y * length + z
                coords[idx] = (x, y, z)
    return coords
