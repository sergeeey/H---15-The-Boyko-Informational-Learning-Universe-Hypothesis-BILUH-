"""Operational finite-propagation front (mathematical_contract.md Sec5.5, G5).

Explicitly NOT a Lieb-Robinson bound -- called "operational
finite-propagation front" everywhere per the contract's naming mandate.

r_q(t) = min { r : sum_{i: dist(source,i) <= r} rho_i(t) >= q }

dist is unweighted hop-distance on the FIXED initial topology M(0) [A15].
rho_i(t) is the carrier-agnostic density (|psi_i(t)|^2 for the quantum
carrier used by every arm except CD, p_i(t) for Arm CD's classical
carrier) -- this module is carrier-agnostic by construction: it only ever
consumes an already-computed non-negative, unit-sum density array.

Multi-source averaging over 5 seed-drawn source nodes per (arm, N, seed)
replicate [A17] needs SeedManager to pick the 5 nodes -- an
experiment-runner concern, Phase 8. This module provides the per-source
primitives plus a pure averaging helper Phase 8 calls once it has the 5
trajectories.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats


def hop_distances_from_source(mask: NDArray[np.bool_], source: int) -> NDArray[np.int64]:
    """BFS shortest hop-distance from `source` to every node on the
    unweighted graph M(0). Unreachable nodes get -1 -- the benchmark's
    population is restricted to connected graphs upstream (estimand.md),
    so downstream functions here reject any -1 rather than silently
    treating it as distance-zero-adjacent."""
    n_nodes = mask.shape[0]
    distances = np.full(n_nodes, -1, dtype=np.int64)
    distances[source] = 0
    frontier = [source]
    while frontier:
        next_frontier: list[int] = []
        for node in frontier:
            for neighbor in np.nonzero(mask[node])[0]:
                neighbor_index = int(neighbor)
                if distances[neighbor_index] == -1:
                    distances[neighbor_index] = distances[node] + 1
                    next_frontier.append(neighbor_index)
        frontier = next_frontier
    return distances


def propagation_front_radius(
    density: NDArray[np.floating], hop_distances: NDArray[np.int64], q: float = 0.9
) -> int:
    """r_q for a single density snapshot rho_i(t)."""
    if np.any(hop_distances < 0):
        raise ValueError("hop_distances contains unreachable (-1) nodes -- graph must be connected")
    max_radius = int(np.max(hop_distances))
    for radius in range(max_radius + 1):
        within_radius = hop_distances <= radius
        if np.sum(density[within_radius]) >= q:
            return radius
    return max_radius


def propagation_front_trajectory(
    density_trajectory: NDArray[np.floating], hop_distances: NDArray[np.int64], q: float = 0.9
) -> NDArray[np.int64]:
    """r_q(t) for every snapshot in a (T+1, N) density trajectory."""
    n_steps = density_trajectory.shape[0]
    radii = np.empty(n_steps, dtype=np.int64)
    for t in range(n_steps):
        radii[t] = propagation_front_radius(density_trajectory[t], hop_distances, q)
    return radii


@dataclass(frozen=True)
class PropagationFrontFit:
    """Everything mathematical_contract.md Sec5.5 requires recorded per run."""

    v_eff: float
    ci_95: tuple[float, float]
    r_squared: float
    fit_window: tuple[int, int]
    saturation_radius: float


def fit_effective_velocity(
    times: NDArray[np.floating],
    radii: NDArray[np.floating],
    fit_window: tuple[int, int],
) -> PropagationFrontFit:
    """Linear fit r_q(t) = v_eff*t + b over the given index window
    [start, end) of `times`/`radii` -- the unsaturated pre-plateau regime.
    Identifying that window automatically from a full trajectory is an
    experiment-runner/FSS concern (Phase 7); here it is an explicit
    caller-supplied parameter, kept simple and independently testable.
    `saturation_radius` is reported from the FULL trajectory (`radii`),
    not just the fit window, per the contract's "where r_q(t) plateaus"
    definition.
    """
    start, end = fit_window
    t_fit = times[start:end]
    r_fit = radii[start:end]
    regression = stats.linregress(t_fit, r_fit)
    v_eff = float(regression.slope)
    r_squared = float(regression.rvalue) ** 2
    n_points = len(t_fit)
    t_critical = float(stats.t.ppf(0.975, df=n_points - 2))
    margin = t_critical * float(regression.stderr)
    ci_95 = (v_eff - margin, v_eff + margin)
    saturation_radius = float(np.max(radii))
    return PropagationFrontFit(
        v_eff=v_eff,
        ci_95=ci_95,
        r_squared=r_squared,
        fit_window=fit_window,
        saturation_radius=saturation_radius,
    )


def average_over_sources(
    trajectories: list[NDArray[np.floating]],
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Mean and (population) std of r_q(t) across multiple source-node
    replicates ([A17] -- 5 sources per (arm, N, seed) in the real
    pipeline). Carrier- and source-count-agnostic: plain array statistics
    over whatever trajectories the caller passes in."""
    stacked = np.stack(trajectories, axis=0)
    mean: NDArray[np.floating] = np.mean(stacked, axis=0)
    std: NDArray[np.floating] = np.std(stacked, axis=0)
    return mean, std
