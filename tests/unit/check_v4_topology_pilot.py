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
from boyko_benchmark.observables.propagation_front import hop_distances_from_source
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
    # rho=0.05/m=3 (not rho=0.1/m=1): found while adding the while-active
    # ICE check (docs/v4_spec.md Sec3) that the more aggressive config
    # reproducibly disconnects this exact fixture on window 0 -- a real
    # ICE, not a wiring bug, but this test's job is checking the
    # trajectory plumbing on a run that actually completes, not exercising
    # ICE truncation (that has its own dedicated tests below).
    rule = RateBasedTopologyRule(
        rho=0.05,
        m=3,
        regrow_scorer=CorrelationScorer(),
        topology_tiebreak_seed=42,
        control_regrowth_seed=42,
    )

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
    assert result.truncated_at_window is None


class _DisconnectAtWindow:
    """ICE-injection fixture (`docs/v4_spec.md` Sec3: "Pruning
    disconnects the graph -> while-active -- truncate the run at that
    window"): a no-op topology rule except on its `disconnect_at`-th
    call, when it deterministically removes edge (0,1) -- a bridge on
    the 4-node path fixture below, disconnecting node 0 from the rest."""

    def __init__(self, disconnect_at: int) -> None:
        self._disconnect_at = disconnect_at
        self._calls = 0

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        self._calls += 1
        if self._calls != self._disconnect_at:
            return graph
        new_mask = graph.mask.copy()
        new_weights = graph.weights.copy()
        new_mask[0, 1] = new_mask[1, 0] = False
        new_weights[0, 1] = new_weights[1, 0] = 0.0
        return WeightedGraph(mask=new_mask, weights=new_weights)


def _path_graph_4() -> WeightedGraph:
    mask = np.zeros((4, 4), dtype=bool)
    weights = np.zeros((4, 4))
    for i, j in [(0, 1), (1, 2), (2, 3)]:
        mask[i, j] = mask[j, i] = True
        weights[i, j] = weights[j, i] = 1.0
    return WeightedGraph(mask=mask, weights=weights)


def test_disconnection_truncates_the_run_at_that_window_and_flags_it() -> None:
    graph = _path_graph_4()
    psi0 = localized_psi0(graph.n_nodes, source_node=3)
    rule = _DisconnectAtWindow(disconnect_at=2)

    result = run_adaptive_dynamics_v4(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        rule,
        dt=0.05,
        k=5,
        dtau_steps=5,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    assert result.truncated_at_window == 1  # 0-indexed: rule's 2nd call happens in window 1
    assert len(result.window_trajectories) == 2
    assert not result.final_graph.mask[0, 1]


class _RecordingTopologyRule:
    """`on_window` regression fixture (V5-K1'-Exposure, `docs/v5_spec.md`
    Sec13): an identity rule that also records the exact graph object it
    returns each call, so a test can confirm `on_window` receives THAT
    SAME post-update object (not a stale copy, not the pre-update graph)
    via identity comparison -- avoids depending on Hebbian adaptation's
    numeric details, which also mutate this same graph earlier each
    window and would make a value-based marker fragile."""

    def __init__(self) -> None:
        self.returned: list[WeightedGraph] = []

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        self.returned.append(graph)
        return graph


def test_on_window_is_called_once_per_window_with_the_post_update_graph() -> None:
    graph = _path_graph_4()
    psi0 = localized_psi0(graph.n_nodes, source_node=3)
    rule = _RecordingTopologyRule()
    recorded: list[tuple[int, WeightedGraph]] = []

    def on_window(window_index: int, current_graph: WeightedGraph) -> None:
        recorded.append((window_index, current_graph))

    run_adaptive_dynamics_v4(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        rule,
        dt=0.05,
        k=5,
        dtau_steps=3,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
        on_window=on_window,
    )

    assert [window_index for window_index, _ in recorded] == [0, 1, 2]
    assert len(rule.returned) == 3
    assert [g for _, g in recorded] == rule.returned


def test_omitting_on_window_reproduces_baseline_exactly() -> None:
    """Regression: default `on_window=None` must not change the result
    at all -- same fixture/params as the existing identity-rule wiring
    test above, re-run once with the new parameter's default."""
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


def test_no_disconnection_means_truncated_at_window_is_none() -> None:
    graph = _path_graph_4()
    psi0 = localized_psi0(graph.n_nodes, source_node=3)
    rule = _DisconnectAtWindow(disconnect_at=100)  # never fires within dtau_steps

    result = run_adaptive_dynamics_v4(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        rule,
        dt=0.05,
        k=5,
        dtau_steps=5,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    assert result.truncated_at_window is None
    assert len(result.window_trajectories) == 5


def test_on_window_still_fires_for_the_truncating_window() -> None:
    """Reviewer-flagged gap (2026-08-18, V5-K1'-Exposure infra review):
    `on_window` is documented as generic/reusable (any future caller, not
    just V5 -- which can never disconnect by construction, `docs/v5_spec.
    md` Sec3), so its behavior on a disconnecting window must be locked
    down by a test, not left implicit. Confirms `on_window` DOES receive
    the disconnected post-update graph for the truncating window -- it
    fires before the connectivity check, exactly as `run_adaptive_
    dynamics_v4`'s own docstring orders it."""
    graph = _path_graph_4()
    psi0 = localized_psi0(graph.n_nodes, source_node=3)
    rule = _DisconnectAtWindow(disconnect_at=2)
    recorded: list[tuple[int, bool]] = []

    def on_window(window_index: int, current_graph: WeightedGraph) -> None:
        connected = bool(np.all(hop_distances_from_source(current_graph.mask, 0) != -1))
        recorded.append((window_index, connected))

    result = run_adaptive_dynamics_v4(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        rule,
        dt=0.05,
        k=5,
        dtau_steps=5,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
        on_window=on_window,
    )

    assert result.truncated_at_window == 1
    assert recorded == [(0, True), (1, False)]
