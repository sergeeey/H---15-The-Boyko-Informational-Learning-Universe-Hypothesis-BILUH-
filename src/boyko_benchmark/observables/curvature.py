"""Phase 12 Stage 3 (docs/phase12_spec.md): Forman-Ricci curvature — a
geometry probe that, unlike G1, requires no plateau to be interpretable.

Motivation: G1 (heat-kernel spectral dimension) has never converged for
open-system Active at any N tested (`[A39]`: 0/80 points), so "is there
geometry-like structure here?" is currently unanswered rather than
answered negatively. Forman-Ricci assigns a curvature to every edge from
a closed-form combinatorial expression — no fitting, no plateau
detection, no convergence criterion that can fail to be met.

Formula (Forman 2003; the graph specialization used by Sreejith et al.
2016), with the standard convention of unit node weights:

    F(e) = w_e * [ (w_u/w_e + w_v/w_e)
                   - sum_{e_u ~ u, e_u != e} w_u / sqrt(w_e * w_{e_u})
                   - sum_{e_v ~ v, e_v != e} w_v / sqrt(w_e * w_{e_v}) ]

For an unweighted graph this collapses to F(e) = 4 - deg(u) - deg(v),
which is what the hand-derived tests pin.

IMPORTANT interpretive caveat, learned from `[A41]`: on this project's
graphs the topology is fixed (`NoTopologyUpdate`, `[A8]`/`[A14]`), so
degrees never change and any cross-cell difference in F comes entirely
from the WEIGHTS. `[A41]` established that a weight-distribution change
alone can masquerade as structure in a graph statistic. Therefore any
curvature comparison between cells MUST be run against the same
weight-shuffle null model (`scripts/run_phase12_weight_shuffle_null.py`)
before being read as structural — this module deliberately does not
provide a "just give me the number" convenience that would encourage
skipping that control.
"""

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.types import WeightedGraph


def forman_ricci_curvature(graph: WeightedGraph) -> NDArray[np.floating]:
    """Per-edge Forman-Ricci curvature, one value per undirected edge
    (upper-triangle order). Node weights are taken as 1.0 throughout —
    the standard convention when a graph carries no independent node
    measure, as here.

    Returns an empty array for a graph with no positive-weight edges.

    **Zero-weight edges are excluded** (`[A42]`): the Hebbian rule's
    non-negativity clamp can drive a weight to exactly zero under noise,
    and `1/sqrt(w_e * w_neighbor)` would then produce inf/nan and poison
    every downstream aggregate. A zero-weight edge carries no coupling —
    it is dynamically absent even though `mask` still records it — so it
    is dropped from the weighted graph rather than regularized with an
    epsilon, which would invent a coupling the dynamics had removed.
    Consequence: the returned array has one entry per POSITIVE-weight
    edge, which may be fewer than `mask`'s edge count.
    """
    weights = graph.weights
    # WHY not `graph.mask`: mask records topology, but a zero weight
    # means no coupling. Using positive weight as the effective edge
    # criterion keeps the formula's domain (strictly positive weights)
    # and the physics (no coupling = no edge) in agreement.
    effective = graph.mask & (weights > 0.0)
    upper = np.argwhere(np.triu(effective))
    if len(upper) == 0:
        return np.zeros(0, dtype=float)

    curvatures = np.zeros(len(upper), dtype=float)
    for index, (i, j) in enumerate(upper):
        edge_weight = weights[i, j]
        incident_sum = 0.0
        for neighbor in np.flatnonzero(effective[i]):
            if neighbor != j:
                incident_sum += 1.0 / np.sqrt(edge_weight * weights[i, neighbor])
        for neighbor in np.flatnonzero(effective[j]):
            if neighbor != i:
                incident_sum += 1.0 / np.sqrt(edge_weight * weights[j, neighbor])
        curvatures[index] = edge_weight * (2.0 / edge_weight - incident_sum)
    return curvatures
