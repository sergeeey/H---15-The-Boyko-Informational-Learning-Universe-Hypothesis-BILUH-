"""M2 (`docs/v4_spec.md` Sec7/Sec8): K1, the damaged-lattice restoration
gate -- a PAIRED comparison, A3 (`CorrelationScorer`) vs A4 (`Distance
StratifiedShuffleScorer`), both regrowing from the IDENTICAL damaged
lattice for a given seed index. `PASS` requires `R_edge(A3) >
R_edge(A4)` (`docs/v4_spec.md` Sec7); this module computes one seed's
pair of results, `experiment/run_k1_gate.py` aggregates across seeds.

Single lattice-center source node ([A25]'s reasoning applies unchanged:
every lattice node has identical local structure, degree-preserving
damage does not break that). Seed streams derived via `SeedManager`
([A11]): `damage_seed` differs per seed index; `topology_tiebreak_seed`/
`control_regrowth_seed` use the same integer for A3 and A4 within one
seed index -- but each arm gets its OWN `RateBasedTopologyRule` instance
(own `Generator` objects), so the pairing only holds byte-for-byte
through the first window where the two graphs actually diverge (`A4`'s
`DistanceStratifiedShuffleScorer` consumes its `rng` via `permutation`;
`A3`'s `CorrelationScorer` never touches its `rng` at all -- [VERIFIED-
grep, `dynamics/topology_v4.py`] `rng.permutation` at line 131,
`CorrelationScorer.score`'s body has no `rng.*` call). Once regrowth
picks different edges, `len(candidates)` differs per arm going forward
and each arm's `Generator` draws a different amount per window from
that point on -- reviewer-found (2026-08-18), independently re-verified
per `audit-verification-gate.md`, corrected here rather than left as an
overclaimed noise-pairing guarantee.
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import (
    CorrelationScorer,
    DistanceStratifiedShuffleScorer,
    RateBasedTopologyRule,
)
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.damage import Edge, corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.observables.edge_recovery import compute_edge_recovery

_K1_DAMAGE_STREAM = 0
_K1_TIEBREAK_STREAM = 1
_K1_REGROWTH_STREAM = 2


@dataclass(frozen=True)
class K1SeedResult:
    seed_index: int
    r_edge_a3: float
    r_edge_a4: float
    wrong_removal_a3: float
    wrong_removal_a4: float
    damaged_out_a3: frozenset[Edge]
    damaged_out_a4: frozenset[Edge]
    truncated_at_window_a3: int | None
    truncated_at_window_a4: int | None


def _lattice_center_index(side_length: int) -> int:
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2, side_length // 2, side_length // 2])
    return int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))


def run_k1_gate_one_seed(
    side_length: int,
    damage_fraction: float,
    rho: float,
    m: int,
    eta: float,
    dt: float,
    k: int,
    dtau_steps: int,
    seed_index: int,
    master_seed: int = 0,
) -> K1SeedResult:
    seed_manager = SeedManager(master_seed)
    graph = generate_periodic_cubic_lattice(side_length)
    original_edges = frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(graph.mask)))
    center_index = _lattice_center_index(side_length)
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, _K1_DAMAGE_STREAM)
    damaged_graph, damaged_out = corrupt_lattice_edges(graph, damage_rng, damage_fraction)

    tiebreak_seed = int(
        seed_manager.child_seed(seed_index, _K1_TIEBREAK_STREAM).generate_state(1)[0]
    )
    regrowth_seed = int(
        seed_manager.child_seed(seed_index, _K1_REGROWTH_STREAM).generate_state(1)[0]
    )

    a3_rule = RateBasedTopologyRule(
        rho=rho,
        m=m,
        regrow_scorer=CorrelationScorer(),
        topology_tiebreak_seed=tiebreak_seed,
        control_regrowth_seed=regrowth_seed,
    )
    result_a3 = run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=eta),
        a3_rule,
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )
    recovery_a3 = compute_edge_recovery(original_edges, damaged_out, result_a3.final_graph.mask)

    a4_rule = RateBasedTopologyRule(
        rho=rho,
        m=m,
        regrow_scorer=DistanceStratifiedShuffleScorer(CorrelationScorer()),
        topology_tiebreak_seed=tiebreak_seed,
        control_regrowth_seed=regrowth_seed,
    )
    result_a4 = run_adaptive_dynamics_v4(
        damaged_graph,
        psi0,
        HebbianAdaptation(eta=eta),
        a4_rule,
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )
    recovery_a4 = compute_edge_recovery(original_edges, damaged_out, result_a4.final_graph.mask)

    return K1SeedResult(
        seed_index=seed_index,
        r_edge_a3=recovery_a3.r_edge,
        r_edge_a4=recovery_a4.r_edge,
        wrong_removal_a3=recovery_a3.wrong_removal_rate,
        wrong_removal_a4=recovery_a4.wrong_removal_rate,
        damaged_out_a3=damaged_out,
        damaged_out_a4=damaged_out,
        truncated_at_window_a3=result_a3.truncated_at_window,
        truncated_at_window_a4=result_a4.truncated_at_window,
    )
