"""Exact degree-constrained-subgraph (b-matching) solver, extracted from
V4-K1c/K1d's capacity audits (`docs/assumptions.md` `[A61]`, `[A63]`):
`M* = max |S|, S subset of eligible_edges, s.t. deg_S(i) <= caps[i]`.

Used to distinguish algorithmic weakness (a good selection exists, the
greedy heuristic in `BoundedIncidenceTopologyRule` just misses it) from
structural incompatibility (no selection close to the target exists,
regardless of selector quality) in V4's K1 gate's exposure failures.
Previously duplicated (with slight variation) between `scripts/run_
k1c_capacity_audit.py` and `run_k1d_capacity_audit.py` with no committed
test locking in the formulation -- reviewer-flagged gap (2026-08-18,
`feat/v4-k1d-reference-degree-cap`), fixed by extracting here with the
tests in `tests/unit/check_capacity_matching.py`.
"""

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

Edge = tuple[int, int]


def max_capacity_cardinality(eligible_edges: frozenset[Edge], caps: dict[int, int]) -> int:
    """Solved via `scipy.optimize.milp`: one binary variable per edge,
    one linear constraint per node (sum of its selected incident edges
    <= its cap), maximizing total selected edges. `milp` minimizes by
    default, so the cost vector is negated; `M*` is recovered as
    `round(-result.fun)`.

    `caps` need only contain entries for nodes actually touched by
    `eligible_edges` -- callers with a fixed reference-degree cap
    (V4-K1d) may pass a larger dict covering every node in the graph;
    only the touched subset is used.
    """
    if not eligible_edges:
        return 0
    edges = list(eligible_edges)
    nodes = sorted({n for e in edges for n in e})

    n_edges = len(edges)
    cost = -np.ones(n_edges)
    incidence = np.array([[1.0 if node in edge else 0.0 for edge in edges] for node in nodes])
    upper_bounds = np.array([caps[node] for node in nodes])
    constraints = LinearConstraint(incidence, -np.inf, upper_bounds)
    integrality = np.ones(n_edges, dtype=np.intp)
    bounds = Bounds(0, 1)

    result = milp(cost, constraints=constraints, integrality=integrality, bounds=bounds)
    if result.status != 0:
        raise RuntimeError(f"max_capacity_cardinality: milp failed, status={result.status}")
    return int(round(-result.fun))
