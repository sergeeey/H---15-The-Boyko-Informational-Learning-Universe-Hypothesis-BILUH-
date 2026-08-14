"""Phase 11 §12.6-12.7: modularity and spectral_conductance. Hand-derived
barbell fixture (two triangles joined by one edge), cross-checked via a
Bash prototype before writing assertions."""

import numpy as np

from boyko_benchmark.observables.conductance import modularity, spectral_conductance
from boyko_benchmark.types import WeightedGraph


def _barbell_graph() -> WeightedGraph:
    """Triangle {0,1,2} -- edge (2,3) -- triangle {3,4,5}. Hand-derived:
    Fiedler bipartition is exactly {0,1,2} vs {3,4,5}, cut=1 (only edge
    (2,3) crosses), vol(S)=vol(Sbar)=7 each -> conductance = 1/7."""
    n = 6
    mask = np.zeros((n, n), dtype=bool)
    weights = np.zeros((n, n))
    for i, j in [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3)]:
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def _complete_graph(n: int) -> WeightedGraph:
    mask = ~np.eye(n, dtype=bool)
    weights = mask.astype(float)
    return WeightedGraph(mask=mask, weights=weights)


def test_spectral_conductance_barbell_matches_hand_derivation() -> None:
    graph = _barbell_graph()

    conductance = spectral_conductance(graph)

    assert abs(conductance - 1.0 / 7.0) < 1e-9


def test_spectral_conductance_complete_graph_is_high() -> None:
    """A complete graph has no good separator -- any bipartition cuts a
    large fraction of edges. Conductance should be close to its high end
    (well above the barbell's 1/7 bottleneck value)."""
    graph = _complete_graph(6)

    conductance = spectral_conductance(graph)

    assert conductance > 0.5


def test_modularity_barbell_shows_real_community_structure() -> None:
    graph = _barbell_graph()

    q = modularity(graph)

    assert q > 0.3  # two obvious triangles, strong community structure


def test_modularity_complete_graph_is_near_zero() -> None:
    """A complete graph has no meaningful community structure -- every
    node is equally connected to every other, so the best partition
    found should show little to no modularity."""
    graph = _complete_graph(6)

    q = modularity(graph)

    assert q < 0.1
