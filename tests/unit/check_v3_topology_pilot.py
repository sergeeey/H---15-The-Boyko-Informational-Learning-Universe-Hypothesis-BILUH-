"""V3 pilot wiring sanity check (`null_results/20260814-open-system-
geometrogenesis.md`) -- run_adaptive_dynamics_with_topology must
reproduce run_adaptive_dynamics_open exactly when the topology rule is
NoTopologyUpdate, and must actually prune edges when it is
PruneZeroWeightTopologyUpdate and a weight hits exactly 0.0."""

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology import NoTopologyUpdate, PruneZeroWeightTopologyUpdate
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.experiment.v3_topology_pilot import run_adaptive_dynamics_with_topology
from boyko_benchmark.graphs.generators import generate_erdos_renyi


def test_no_topology_update_matches_open_pilot_exactly() -> None:
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
    with_topology = run_adaptive_dynamics_with_topology(
        graph,
        psi0,
        HebbianAdaptation(eta=eta),
        NoTopologyUpdate(),
        dt,
        k,
        dtau_steps,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    np.testing.assert_allclose(
        baseline.final_graph.weights, with_topology.final_graph.weights, atol=1e-12
    )
    np.testing.assert_array_equal(baseline.final_graph.mask, with_topology.final_graph.mask)


def test_prune_rule_can_actually_remove_an_edge_over_a_real_run() -> None:
    """Not just a unit test of the rule in isolation -- confirms the
    wiring actually applies it inside the real adaptation loop. Uses a
    tiny, sparse, high-eta setup so at least one edge is very likely to
    be driven to zero within a short run (this is a wiring check, not a
    claim about typical pilot-budget prune rates -- that is measured
    separately by the actual V3 experiment script)."""
    rng = np.random.default_rng(3)
    graph = generate_erdos_renyi(n_nodes=6, n_edges=8, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)

    result = run_adaptive_dynamics_with_topology(
        graph,
        psi0,
        HebbianAdaptation(eta=5.0),
        PruneZeroWeightTopologyUpdate(),
        dt=0.05,
        k=20,
        dtau_steps=20,
        backend=ClosedUnitaryBackend(),
        gamma=0.0,
        sigma=0.0,
        noise_seed=None,
    )

    n_edges_before = int(graph.mask.sum()) // 2
    n_edges_after = int(result.final_graph.mask.sum()) // 2
    assert n_edges_after <= n_edges_before
    assert n_edges_after < n_edges_before, "expected at least one edge pruned at high eta"
    # Every remaining edge must have strictly positive weight -- the
    # invariant the rule exists to enforce.
    remaining_weights = result.final_graph.weights[np.triu(result.final_graph.mask)]
    assert np.all(remaining_weights > 0.0)
