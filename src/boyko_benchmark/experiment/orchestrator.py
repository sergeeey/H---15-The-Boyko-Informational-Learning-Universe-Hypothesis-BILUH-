"""Runs all requested arms for ONE (N, seed) replicate -- the atomic unit
the FSS grid (mathematical_contract.md Sec6) iterates over.

Multi-size/multi-seed sweeping and cross-replicate statistics aggregation
are the caller's job (Phase 9/10 reporting layer); this module produces
one replicate's raw per-arm results, nothing more.
"""

from dataclasses import dataclass

from boyko_benchmark.arms.shared_initialization import build_shared_initialization
from boyko_benchmark.config import Arm, ExperimentConfig
from boyko_benchmark.experiment.arms_runner import (
    ArmRunResult,
    run_arm_active,
    run_arm_alternative_objective,
    run_arm_classical_diffusion_control,
    run_arm_fixed_flat_geometry,
    run_arm_frozen,
    run_arm_parameter_matched_random,
    run_arm_topology_scrambled,
)
from boyko_benchmark.experiment.operator_independence import run_operator_independence_diagnostic
from boyko_benchmark.experiment.runner import AdaptiveRunResult
from boyko_benchmark.experiment.seed_manager import SeedManager

MEAN_DEGREE_TARGET = 6
"""[A7]: Active/Frozen/AltObjective/CD's shared Erdos-Renyi topology is
mean-degree-matched to Arm E's cubic lattice (2*dimension = 6 neighbors
per node), not chosen independently."""


def n_edges_for_mean_degree(n_nodes: int, mean_degree: int = MEAN_DEGREE_TARGET) -> int:
    """sum(degree) = 2*n_edges = mean_degree*n_nodes."""
    return (n_nodes * mean_degree) // 2


@dataclass(frozen=True)
class ReplicateResult:
    n_nodes: int
    seed_index: int
    arm_results: dict[Arm, ArmRunResult]
    operator_independence_result: AdaptiveRunResult | None


def run_replicate(config: ExperimentConfig, n_nodes: int, seed_index: int) -> ReplicateResult:
    """One (N, seed) replicate across every arm named in `config.arms`.

    Seed paths are keyed `(n_nodes, seed_index, role)` -- order-independent
    per SeedManager's own design, so adding/removing arms from `config.arms`
    never perturbs another arm's seed stream.
    """
    seed_manager = SeedManager(config.experiment.master_seed)
    n_edges = n_edges_for_mean_degree(n_nodes)
    dt = config.fast_dynamics.dt
    k = config.adaptation.K
    dtau_steps = config.adaptation.dtau_steps
    eta = config.adaptation.eta
    n_source_nodes = config.propagation_front.n_source_nodes

    shared_init_rng = seed_manager.child_generator(n_nodes, seed_index, 0)
    shared_init = build_shared_initialization(n_nodes, n_edges, shared_init_rng, n_source_nodes)

    arm_results: dict[Arm, ArmRunResult] = {}

    if Arm.ACTIVE in config.arms:
        arm_results[Arm.ACTIVE] = run_arm_active(shared_init, eta, dt, k, dtau_steps)
    if Arm.FROZEN in config.arms:
        arm_results[Arm.FROZEN] = run_arm_frozen(shared_init, dt, k, dtau_steps)
    if Arm.ALTERNATIVE_OBJECTIVE in config.arms:
        arm_results[Arm.ALTERNATIVE_OBJECTIVE] = run_arm_alternative_objective(
            shared_init, eta, dt, k, dtau_steps
        )
    if Arm.CLASSICAL_DIFFUSION_CONTROL in config.arms:
        arm_results[Arm.CLASSICAL_DIFFUSION_CONTROL] = run_arm_classical_diffusion_control(
            shared_init, eta, dt, k, dtau_steps
        )
    if Arm.PARAMETER_MATCHED_RANDOM in config.arms:
        random_rng = seed_manager.child_generator(n_nodes, seed_index, 1)
        arm_results[Arm.PARAMETER_MATCHED_RANDOM] = run_arm_parameter_matched_random(
            n_nodes, n_edges, random_rng, n_source_nodes, dt, k, dtau_steps
        )
    if Arm.FIXED_FLAT_GEOMETRY in config.arms:
        side_length = round(n_nodes ** (1.0 / 3.0))
        arm_results[Arm.FIXED_FLAT_GEOMETRY] = run_arm_fixed_flat_geometry(
            side_length, dt, k, dtau_steps
        )
    if Arm.TOPOLOGY_SCRAMBLED in config.arms:
        if Arm.ACTIVE not in arm_results:
            raise ValueError(
                "Arm.TOPOLOGY_SCRAMBLED requires Arm.ACTIVE's result ([A8]: derived "
                "from Active's final graph) -- add 'active' to config.arms"
            )
        scramble_rng = seed_manager.child_generator(n_nodes, seed_index, 2)
        n_swaps = config.topology_scrambled.n_swaps_per_edge * n_edges
        arm_results[Arm.TOPOLOGY_SCRAMBLED] = run_arm_topology_scrambled(
            arm_results[Arm.ACTIVE], scramble_rng, n_swaps, dt, k, dtau_steps
        )

    operator_independence_result = None
    if config.fast_dynamics.operator_independence_diagnostic and Arm.ACTIVE in config.arms:
        operator_independence_result = run_operator_independence_diagnostic(
            shared_init, eta, dt, k, dtau_steps
        )

    return ReplicateResult(n_nodes, seed_index, arm_results, operator_independence_result)
