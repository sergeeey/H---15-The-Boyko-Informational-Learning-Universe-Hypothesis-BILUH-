#!/usr/bin/env python
"""V4-K1c capacity audit (user-directed, 2026-08-18, following `[A60]`'s
ICE-1=0.254 exposure failure) -- feasibility-only, no `R_edge`/G1/
curvature/scientific outcome. Distinguishes two hypotheses for WHY
exposure is so low:

  H-A (model incompatibility): persistence + the per-node incidence cap
       make it MATHEMATICALLY IMPOSSIBLE to select `m = round(rho*|E|)`
       edges from the eligible set this window, regardless of selector.
  H-B (algorithmic weakness): a feasible near-`m` selection EXISTS, but
       `BoundedIncidenceTopologyRule`'s deterministic greedy walk picks
       it poorly.

Computed by solving, per window, the EXACT maximum-cardinality
capacitated selection problem (`M*`, a small integer program -- each
window's eligible set is tiny, <=~20 edges, well within `scipy.optimize.
milp`'s reach) and comparing it against the greedy's actual count
(`M_greedy`, already known from `[A60]`'s own run). Reruns the IDENTICAL
5 seeds/damaged lattices/windows (same master_seed=20260818) -- bit-for-
bit reproducible, independently confirmed by this session's reviewer
agent for the K1c run this audits.

Only arm A3 is run: pruning selection depends only on `graph.weights`
and the persistence/cap machinery, never on the regrow scorer
(established fact, `[A57]`-`[A59]`; A3 and A4 disconnect identically in
every prior K1/K1c run). Auditing one arm is sufficient and halves
compute for no loss of diagnostic power.
"""

import sys

import numpy as np
from numpy.typing import NDArray

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
from boyko_benchmark.observables.capacity_matching import (
    max_capacity_cardinality as _solve_max_capacity_cardinality,
)
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
MASTER_SEED = 20260818  # identical to K1c/[A60] -- SAME damaged lattices

_K1_DAMAGE_STREAM = 0
_K1_TIEBREAK_STREAM = 1
_K1_REGROWTH_STREAM = 2


def max_capacity_cardinality(
    eligible_edges: frozenset[Edge], mask: NDArray[np.bool_], q: float, d_min: int = 1
) -> int:
    """K1c-specific wrapper: derives per-node caps from CURRENT degree
    (read off `mask`) via `bounded_incidence_cap`, then delegates the
    actual exact solve to `observables/capacity_matching.py`'s tested,
    shared `max_capacity_cardinality` (formulation locked in by
    `tests/unit/check_capacity_matching.py`'s hand-derived triangle
    case -- previously only a docstring claim with no committed test,
    reviewer-flagged 2026-08-18)."""
    if not eligible_edges:
        return 0
    nodes = sorted({n for e in eligible_edges for n in e})
    caps = {n: bounded_incidence_cap(int(mask[n].sum()), q, d_min) for n in nodes}
    return _solve_max_capacity_cardinality(eligible_edges, caps)


class _CapacityAuditRule:
    """Delegates to a real `BoundedIncidenceTopologyRule`, additionally
    solving `max_capacity_cardinality` per window -- duck-typed
    `StatefulTopologyRule`, driven by the SAME `run_adaptive_dynamics_v4`
    loop the real K1c campaign used (reused unchanged, including its
    while-active connectivity truncation)."""

    def __init__(self, inner: BoundedIncidenceTopologyRule, rho: float, q: float) -> None:
        self._inner = inner
        self._rho = rho
        self._q = q
        self._window_index = 0
        self.records: list[dict[str, int]] = []

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        n_edges = int(graph.mask.sum()) // 2
        n_target = max(1, round(self._rho * n_edges)) if n_edges > 0 else 0
        pre_mask = graph.mask.copy()

        result = self._inner.update(graph, trajectory, dtau)

        eligible = self._inner.last_eligible
        m_star = max_capacity_cardinality(eligible, pre_mask, self._q, D_MIN)
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
    )
    audit_rule = _CapacityAuditRule(inner_rule, RHO, Q)

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
    print("=== V4-K1c capacity audit: exact M* vs greedy M_greedy ===")
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
    print(f"CR_greedy = M_greedy/m = {cr_greedy:.4f}  (should match [A60]'s ICE-1 = 0.254)")
    print(f"ECR  = eligible/m = {ecr:.4f}")
    print(f"CCR  = M*/eligible = {ccr:.4f}")

    print()
    print("=== Diagnosis ===")
    if cr_star >= 0.95:
        print(
            f"CR* = {cr_star:.4f} >= 0.95 but greedy only achieves {cr_greedy:.4f} "
            "=> ALGORITHMIC FAILURE. The constraints are NOT the bottleneck -- "
            "a near-full-exposure selection exists but the greedy selector misses it. "
            "Fix the selector, re-run K1c with the SAME q=0.5, no new physical hypothesis needed."
        )
    else:
        print(
            f"CR* = {cr_star:.4f} -- even the EXACT optimum cannot reach 0.95 exposure "
            "=> STRUCTURAL INCOMPATIBILITY (H-A). persistence + incidence cap + rho are "
            "mutually incompatible at this scale, regardless of selector quality. "
            "A new pre-registered mechanism (e.g. V4-K1d, reference-degree cap) is warranted."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
