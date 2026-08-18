"""V4 loop wiring sanity check (`docs/v4_spec.md` M1): `run_adaptive_
dynamics_v4` must reproduce `run_adaptive_dynamics_open` exactly when
the topology rule is a no-op, confirming the extra `trajectory` plumbing
doesn't change anything else about the loop."""

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation, StateTrajectory
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.v4_topology_pilot import run_adaptive_dynamics_v4
from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.types import WeightedGraph


class _IdentityTopologyRule:
    """Wiring-check-only fixture: does nothing, unlike any real V4 arm
    (which always changes at least one edge per window, `topology_v4.py`'s
    `max(1, ...)` floor) -- exists purely to isolate "does the loop plumb
    trajectory/state correctly" from "does the topology rule do anything"."""

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        return graph


def test_identity_topology_rule_matches_open_pilot_exactly() -> None:
    rng = np.random.default_rng(7)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=16, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)
    dt, k, dtau_steps, eta = 0.05, 10, 5, 0.1

    baseline = run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=eta),
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )
    v4_result = run_adaptive_dynamics_v4(
        graph,
        psi0,
        HebbianAdaptation(eta=eta),
        _IdentityTopologyRule(),
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    np.testing.assert_allclose(
        baseline.final_graph.weights, v4_result.final_graph.weights, atol=1e-12
    )
    np.testing.assert_array_equal(baseline.final_graph.mask, v4_result.final_graph.mask)


def test_real_rate_based_rule_actually_changes_topology_over_a_real_run() -> None:
    """Confirms the wiring passes a REAL trajectory through to the
    topology rule (not, say, an empty or stale one) by using
    CorrelationScorer, which would raise/behave incoherently on a
    malformed trajectory, and checking edges actually change."""
    from boyko_benchmark.dynamics.topology_v4 import CorrelationScorer, RateBasedTopologyRule

    rng = np.random.default_rng(11)
    graph = generate_erdos_renyi(n_nodes=20, n_edges=40, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)
    rule = RateBasedTopologyRule(rho=0.1, m=1, regrow_scorer=CorrelationScorer(), rng_seed=42)

    result = run_adaptive_dynamics_v4(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        rule,
        dt=0.05,
        k=10,
        dtau_steps=5,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    assert not np.array_equal(result.final_graph.mask, graph.mask), "topology never changed"
    n_before = int(graph.mask.sum()) // 2
    n_after = int(result.final_graph.mask.sum()) // 2
    assert n_after == n_before, "edge count should be conserved (matched budget)"
