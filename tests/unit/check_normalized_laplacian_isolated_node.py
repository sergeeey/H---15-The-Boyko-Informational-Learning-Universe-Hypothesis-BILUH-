"""Regression test for the development.yaml run failure (2026-08-13):

Hebbian adaptation (dynamics/adaptive.py) can decay all of a node's weights
toward zero over a long adaptation budget (dtau_steps=200), leaving that
node with degree=0 while its mask edges are still present (topology is
untouched by HebbianAdaptation -- only weights decay). normalized_laplacian
(graphs/weights.py) then computes 1.0/sqrt(0) = inf, propagating NaN into
the returned matrix and, downstream, into WeightedGraph's symmetry check
(NaN is never allclose to NaN, so the *symptom* observed was a spurious
"weights must be symmetric" ValueError -- the real defect is upstream,
here).

This does not decide what a degree-0 node *should* mean physically --
that is a docs/mathematical_contract.md / assumptions.md question. This
test only pins the immediate, uncontroversial requirement: the function
must not silently manufacture inf/nan on a legal (0,1]-degree WeightedGraph
input, since a zero-weight node is a legal state under `[A5]`'s
non-negativity floor.
"""

import numpy as np

from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.types import WeightedGraph


def _path_graph_3_nodes_isolated_middle_weight() -> WeightedGraph:
    """0 - 1 - 2 topology (mask), but node 1's weights have decayed to 0.0.

    Legal WeightedGraph: mask requires an edge, weights=0.0 satisfies
    `weight present without a topology edge` (0.0 is not > 0) and
    non-negativity. This is exactly the state HebbianAdaptation's decay
    term can reach after enough dtau steps.
    """
    mask = np.array([[False, True, False], [True, False, True], [False, True, False]])
    weights = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    return WeightedGraph(mask=mask, weights=weights)


def test_normalized_laplacian_no_nan_on_zero_degree_node() -> None:
    graph = _path_graph_3_nodes_isolated_middle_weight()
    l_norm = normalized_laplacian(graph)

    assert np.all(np.isfinite(l_norm)), (
        f"normalized_laplacian produced non-finite entries for a zero-degree node:\n{l_norm}"
    )


def test_normalized_laplacian_symmetric_on_zero_degree_node() -> None:
    graph = _path_graph_3_nodes_isolated_middle_weight()
    l_norm = normalized_laplacian(graph)

    np.testing.assert_allclose(l_norm, l_norm.T, atol=1e-12)
