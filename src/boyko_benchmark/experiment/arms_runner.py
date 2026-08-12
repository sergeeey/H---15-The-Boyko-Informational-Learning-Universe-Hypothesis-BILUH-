"""Per-arm dynamics+adaptation runners (mathematical_contract.md Sec4).

Each function wires graph construction ([A6] localized initial state,
SharedInitialization or an independent draw) + the Cycle-15 core loop
(experiment/runner.py) into one arm's result. Arm D (Topology Scrambled)
is deliberately NOT here -- it needs Active's FINAL graph as input
(`[A8]`), so it can only be constructed after Arm A's run completes
(Phase 8 Cycle 17).
"""

from dataclasses import dataclass

import numpy as np

from boyko_benchmark.arms.shared_initialization import (
    SharedInitialization,
    build_parameter_matched_random_graph,
)
from boyko_benchmark.config import Arm
from boyko_benchmark.dynamics.adaptive import (
    AlternativeObjective,
    ClassicalHebbianAdaptation,
    HebbianAdaptation,
    NoAdaptation,
)
from boyko_benchmark.experiment.runner import (
    AdaptiveRunResult,
    localized_p0,
    localized_psi0,
    run_adaptive_dynamics,
    run_adaptive_dynamics_classical,
)
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.graphs.rewiring import scramble_preserving_degree_sequence
from boyko_benchmark.types import WeightedGraph


@dataclass(frozen=True)
class ArmRunResult:
    arm: Arm
    initial_graph: WeightedGraph
    dynamics_result: AdaptiveRunResult
    source_nodes: tuple[int, ...]


def run_arm_active(
    shared_init: SharedInitialization, eta: float, dt: float, k: int, dtau_steps: int
) -> ArmRunResult:
    psi0 = localized_psi0(shared_init.graph.n_nodes, shared_init.source_nodes[0])
    result = run_adaptive_dynamics(
        shared_init.graph, psi0, HebbianAdaptation(eta=eta), dt, k, dtau_steps
    )
    return ArmRunResult(Arm.ACTIVE, shared_init.graph, result, shared_init.source_nodes)


def run_arm_frozen(
    shared_init: SharedInitialization, dt: float, k: int, dtau_steps: int
) -> ArmRunResult:
    psi0 = localized_psi0(shared_init.graph.n_nodes, shared_init.source_nodes[0])
    result = run_adaptive_dynamics(shared_init.graph, psi0, NoAdaptation(), dt, k, dtau_steps)
    return ArmRunResult(Arm.FROZEN, shared_init.graph, result, shared_init.source_nodes)


def run_arm_alternative_objective(
    shared_init: SharedInitialization, eta: float, dt: float, k: int, dtau_steps: int
) -> ArmRunResult:
    psi0 = localized_psi0(shared_init.graph.n_nodes, shared_init.source_nodes[0])
    result = run_adaptive_dynamics(
        shared_init.graph, psi0, AlternativeObjective(eta=eta), dt, k, dtau_steps
    )
    return ArmRunResult(
        Arm.ALTERNATIVE_OBJECTIVE, shared_init.graph, result, shared_init.source_nodes
    )


def run_arm_classical_diffusion_control(
    shared_init: SharedInitialization, eta: float, dt: float, k: int, dtau_steps: int
) -> ArmRunResult:
    p0 = localized_p0(shared_init.graph.n_nodes, shared_init.source_nodes[0])
    result = run_adaptive_dynamics_classical(
        shared_init.graph, p0, ClassicalHebbianAdaptation(eta=eta), dt, k, dtau_steps
    )
    return ArmRunResult(
        Arm.CLASSICAL_DIFFUSION_CONTROL, shared_init.graph, result, shared_init.source_nodes
    )


def run_arm_parameter_matched_random(
    n_nodes: int,
    n_edges: int,
    rng: np.random.Generator,
    n_source_nodes: int,
    dt: float,
    k: int,
    dtau_steps: int,
) -> ArmRunResult:
    """[A7]: independent Erdos-Renyi draw, NOT sharing SharedInitialization
    -- source nodes are therefore also independently drawn from this arm's
    own rng stream, not inherited from Active."""
    graph = build_parameter_matched_random_graph(n_nodes, n_edges, rng)
    n_to_draw = min(n_source_nodes, n_nodes)
    source_nodes = tuple(int(i) for i in rng.choice(n_nodes, size=n_to_draw, replace=False))
    psi0 = localized_psi0(n_nodes, source_nodes[0])
    result = run_adaptive_dynamics(graph, psi0, NoAdaptation(), dt, k, dtau_steps)
    return ArmRunResult(Arm.PARAMETER_MATCHED_RANDOM, graph, result, source_nodes)


def run_arm_fixed_flat_geometry(
    side_length: int, dt: float, k: int, dtau_steps: int
) -> ArmRunResult:
    """[A25]: single lattice-center source node, NOT [A17]'s 5-source
    average -- every lattice node has identical degree/local structure, so
    the seed-dependent-degree confound [A17] was built to remove does not
    exist here. `NoAdaptation` per Sec4's arm table (dynamics on, weights
    never change -- positive geometric calibration, never an optimization
    target)."""
    graph = generate_periodic_cubic_lattice(side_length)
    coords = lattice_coordinates(side_length)
    center_coord = np.array([side_length // 2, side_length // 2, side_length // 2])
    center_index = int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))
    psi0 = localized_psi0(graph.n_nodes, center_index)
    result = run_adaptive_dynamics(graph, psi0, NoAdaptation(), dt, k, dtau_steps)
    return ArmRunResult(Arm.FIXED_FLAT_GEOMETRY, graph, result, (center_index,))


def run_arm_topology_scrambled(
    active_result: ArmRunResult,
    rng: np.random.Generator,
    n_swaps: int,
    dt: float,
    k: int,
    dtau_steps: int,
) -> ArmRunResult:
    """[A8]: derived from Active's FINAL graph -- the post-adaptation
    topology is rewired (one-shot, degree-preserving), not the initial
    one. `NoAdaptation` afterward (Sec4 arm table: dynamics on
    post-scramble, weights frozen). `source_nodes` reuse Active's own set
    unchanged -- a degree-preserving rewire only shuffles EDGES, node
    indices persist through it, so "the same node" has a real meaning
    here unlike Arm C's independent draw ([A7], no shared node identity)."""
    active_final_graph = active_result.dynamics_result.final_graph
    scrambled_graph = scramble_preserving_degree_sequence(active_final_graph, rng, n_swaps)
    psi0 = localized_psi0(scrambled_graph.n_nodes, active_result.source_nodes[0])
    result = run_adaptive_dynamics(scrambled_graph, psi0, NoAdaptation(), dt, k, dtau_steps)
    return ArmRunResult(Arm.TOPOLOGY_SCRAMBLED, scrambled_graph, result, active_result.source_nodes)
