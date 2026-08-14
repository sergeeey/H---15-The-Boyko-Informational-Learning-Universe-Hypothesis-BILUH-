"""Phase 11 T4 (ТЗ §22): seed reproducibility. Same noise_seed -> bit-
identical trajectory; different noise_seed -> different trajectory (the
latter already covered by T9, re-verified here at the open_pilot level
for the derived-per-window seed scheme, ТЗ §8)."""

import numpy as np

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.dynamics.open_dynamics import PhenomenologicalOpenBackend
from boyko_benchmark.experiment.open_pilot import run_adaptive_dynamics_open
from boyko_benchmark.experiment.runner import localized_psi0
from boyko_benchmark.graphs.generators import generate_erdos_renyi


def test_t4_same_backend_seed_gives_identical_trajectory() -> None:
    hamiltonian = np.array([[1.0, -1.0], [-1.0, 1.0]])
    psi0 = np.array([1.0, 0.0], dtype=complex)

    trajectory_1 = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, 0.1, 20, gamma=0.0, sigma=0.3, noise_seed=99
    )
    trajectory_2 = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, 0.1, 20, gamma=0.0, sigma=0.3, noise_seed=99
    )

    np.testing.assert_array_equal(trajectory_1, trajectory_2)


def test_t4_different_backend_seeds_give_different_trajectories() -> None:
    hamiltonian = np.array([[1.0, -1.0], [-1.0, 1.0]])
    psi0 = np.array([1.0, 0.0], dtype=complex)

    trajectory_1 = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, 0.1, 20, gamma=0.0, sigma=0.3, noise_seed=1
    )
    trajectory_2 = PhenomenologicalOpenBackend().evolve(
        hamiltonian, psi0, 0.1, 20, gamma=0.0, sigma=0.3, noise_seed=2
    )

    assert not np.allclose(trajectory_1, trajectory_2)


def test_t4_same_open_pilot_noise_seed_gives_identical_final_graph() -> None:
    """Reproducibility at the adaptation-loop level: run_adaptive_
    dynamics_open derives a fresh per-window sub-seed from one top-level
    noise_seed via SeedSequence.spawn (ТЗ §8) -- the WHOLE run must be
    reproducible from that one seed, not just a single window."""
    rng = np.random.default_rng(5)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=16, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)

    kwargs = dict(
        dt=0.05,
        k=10,
        dtau_steps=5,
        backend=PhenomenologicalOpenBackend(),
        gamma=0.0,
        sigma=0.2,
        noise_seed=42,
    )
    result_1 = run_adaptive_dynamics_open(graph, psi0, HebbianAdaptation(eta=0.1), **kwargs)
    result_2 = run_adaptive_dynamics_open(graph, psi0, HebbianAdaptation(eta=0.1), **kwargs)

    np.testing.assert_array_equal(result_1.final_graph.weights, result_2.final_graph.weights)


def test_t4_different_open_pilot_noise_seed_gives_different_final_graph() -> None:
    rng = np.random.default_rng(5)
    graph = generate_erdos_renyi(n_nodes=8, n_edges=16, rng=rng)
    psi0 = localized_psi0(graph.n_nodes, source_node=0)

    result_1 = run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        dt=0.05,
        k=10,
        dtau_steps=5,
        backend=PhenomenologicalOpenBackend(),
        gamma=0.0,
        sigma=0.2,
        noise_seed=1,
    )
    result_2 = run_adaptive_dynamics_open(
        graph,
        psi0,
        HebbianAdaptation(eta=0.1),
        dt=0.05,
        k=10,
        dtau_steps=5,
        backend=PhenomenologicalOpenBackend(),
        gamma=0.0,
        sigma=0.2,
        noise_seed=2,
    )

    assert not np.allclose(result_1.final_graph.weights, result_2.final_graph.weights)
