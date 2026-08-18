#!/usr/bin/env python
"""V4-K1d capacity audit (following the real K1d campaign's ICE-1=0.487
exposure failure) -- feasibility-only, no `R_edge`/G1/curvature. Same
H-A/H-B distinction as `[A61]`'s K1c audit
(`scripts/run_k1c_capacity_audit.py`), re-run for K1d's DIFFERENT
(fixed, non-drifting) per-node caps -- `docs/v4_spec.md` Sec7e's own
text requires this before any further pre-registration if K1d's
exposure also fails: "if even the exact optimum ... cannot reach 0.95
exposure under the reference-degree cap, that is a new finding
requiring the same [A61]-style capacity audit."

  H-A (model incompatibility): persistence + the FIXED per-node cap
       make it MATHEMATICALLY IMPOSSIBLE to select `m` edges this
       window, regardless of selector.
  H-B (algorithmic weakness): a feasible near-`m` selection EXISTS
       under the fixed caps, but the greedy walk picks it poorly.

Reruns the IDENTICAL 5 seeds/damaged lattices as K1/K1c/K1d (same
master_seed=20260818), arm A3 only (pruning selection is scorer-
independent, established `[A57]`-`[A59]`).
"""

import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation, StateTrajectory
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import (
    BoundedIncidenceTopologyRule,
    CorrelationScorer,
    bounded_incidence_cap,
)
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.damage import Edge, corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.types import WeightedGraph

N_SIDE_LENGTH = 8  # N = 512
N_SEEDS = 5
DAMAGE_FRACTION = 0.10
RHO = 0.01
M_PERSISTENCE = 3
Q = 0.5
D_MIN = 1
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
DTAU_STEPS = 50
MASTER_SEED = 20260818  # identical to K1/K1c/K1d -- SAME damaged lattices

_K1_DAMAGE_STREAM = 0
_K1_TIEBREAK_STREAM = 1
_K1_REGROWTH_STREAM = 2


def max_capacity_cardinality(eligible_edges: frozenset[Edge], caps: dict[int, int]) -> int:
    """Exact `M* = max |S|, S subset of eligible_edges, s.t. deg_S(i) <=
    caps[i]` -- same ILP formulation as `run_k1c_capacity_audit.py`'s
    version (sanity-checked there on a hand-worked triangle example),
    generalized to take `caps` directly rather than recomputing from a
    mask -- K1d's caps are FIXED (reference-degree), not recomputed
    from the current graph each window."""
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


class _CapacityAuditRule:
    """Delegates to a real `BoundedIncidenceTopologyRule` (constructed
    with `reference_degrees`), additionally solving `max_capacity_
    cardinality` per window using the SAME fixed reference caps the
    real rule uses."""

    def __init__(
        self,
        inner: BoundedIncidenceTopologyRule,
        rho: float,
        reference_caps: dict[int, int],
    ) -> None:
        self._inner = inner
        self._rho = rho
        self._reference_caps = reference_caps
        self._window_index = 0
        self.records: list[dict[str, int]] = []

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        n_edges = int(graph.mask.sum()) // 2
        n_target = max(1, round(self._rho * n_edges)) if n_edges > 0 else 0

        result = self._inner.update(graph, trajectory, dtau)

        eligible = self._inner.last_eligible
        m_star = max_capacity_cardinality(eligible, self._reference_caps)
        m_greedy = len(self._inner.last_pruned)

        self.records.append(
            {
                "window": self._window_index,
                "n_target": n_target,
                "n_eligible": len(eligible),
                "m_star": m_star,
                "m_greedy": m_greedy,
            }
        )
        self._window_index += 1
        return result


def _lattice_center_index(side_length: int) -> int:
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2] * 3)
    return int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))


def audit_one_seed(seed_index: int) -> list[dict[str, int]]:
    seed_manager = SeedManager(MASTER_SEED)
    graph = generate_periodic_cubic_lattice(N_SIDE_LENGTH)
    center_index = _lattice_center_index(N_SIDE_LENGTH)
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, _K1_DAMAGE_STREAM)
    damaged_graph, _damaged_out = corrupt_lattice_edges(graph, damage_rng, DAMAGE_FRACTION)

    reference_degrees = {
        node: int(damaged_graph.mask[node].sum()) for node in range(damaged_graph.n_nodes)
    }
    reference_caps = {
        node: bounded_incidence_cap(degree, Q, D_MIN) for node, degree in reference_degrees.items()
    }

    tiebreak_seed = int(
        seed_manager.child_seed(seed_index, _K1_TIEBREAK_STREAM).generate_state(1)[0]
    )
    regrowth_seed = int(
        seed_manager.child_seed(seed_index, _K1_REGROWTH_STREAM).generate_state(1)[0]
    )

    inner_rule = BoundedIncidenceTopologyRule(
        rho=RHO,
        m=M_PERSISTENCE,
        q=Q,
        regrow_scorer=CorrelationScorer(),
        topology_tiebreak_seed=tiebreak_seed,
        control_regrowth_seed=regrowth_seed,
        reference_degrees=reference_degrees,
    )
    audit_rule = _CapacityAuditRule(inner_rule, RHO, reference_caps)

    run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=ETA),
        audit_rule,
        DT,
        K_SUBSTEPS,
        DTAU_STEPS,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )
    return audit_rule.records


def main() -> int:
    print("=== V4-K1d capacity audit: exact M* vs greedy M_greedy (fixed reference caps) ===")
    print(f"N={N_SIDE_LENGTH**3}, rho={RHO}, m={M_PERSISTENCE}, q={Q}, arm=A3 only")
    print()
    header = f"{'seed':>4} {'win':>3} {'target(m)':>9} {'eligible':>8} {'M*':>4} {'M_greedy':>8}"
    print(header)

    all_records = []
    for seed_index in range(N_SEEDS):
        records = audit_one_seed(seed_index)
        for r in records:
            print(
                f"{seed_index:>4} {r['window']:>3} {r['n_target']:>9} {r['n_eligible']:>8} "
                f"{r['m_star']:>4} {r['m_greedy']:>8}"
            )
        all_records.extend(records)

    warmup = M_PERSISTENCE - 1
    post_warmup = [r for r in all_records if r["window"] >= warmup]

    target_total = sum(r["n_target"] for r in post_warmup)
    eligible_total = sum(r["n_eligible"] for r in post_warmup)
    m_star_total = sum(r["m_star"] for r in post_warmup)
    m_greedy_total = sum(r["m_greedy"] for r in post_warmup)

    cr_star = m_star_total / target_total if target_total else float("nan")
    cr_greedy = m_greedy_total / target_total if target_total else float("nan")
    ecr = eligible_total / target_total if target_total else float("nan")
    ccr = m_star_total / eligible_total if eligible_total else float("nan")

    print()
    print("=== Aggregate (excluding first m-1 warmup windows, same convention as ICE-1) ===")
    print(f"target_total (sum m)      = {target_total}")
    print(f"eligible_total            = {eligible_total}")
    print(f"M*_total (exact optimum)  = {m_star_total}")
    print(f"M_greedy_total (actual)   = {m_greedy_total}")
    print(f"CR*  = M*/m       = {cr_star:.4f}")
    print(f"CR_greedy = M_greedy/m = {cr_greedy:.4f}")
    print(f"ECR  = eligible/m = {ecr:.4f}")
    print(f"CCR  = M*/eligible = {ccr:.4f}")

    print()
    print("=== Diagnosis ===")
    if cr_star >= 0.95:
        print(
            f"CR* = {cr_star:.4f} >= 0.95 but greedy only achieves {cr_greedy:.4f} "
            "=> ALGORITHMIC FAILURE. Fix the selector, re-run K1d with the SAME q=0.5."
        )
    else:
        print(
            f"CR* = {cr_star:.4f} -- even the EXACT optimum cannot reach 0.95 exposure "
            "=> STRUCTURAL INCOMPATIBILITY (H-A), same as K1c's [A61] finding. The fixed "
            "reference-degree cap improved exposure over K1c but did not resolve the "
            "underlying incompatibility between persistence, the incidence cap, and rho."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
