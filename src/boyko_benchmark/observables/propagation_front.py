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


def detect_unsaturated_window(radii: NDArray[np.int64]) -> tuple[int, int]:
    """Finds the pre-plateau fit window `mathematical_contract.md:508`
    requires ("Fit, over the unsaturated (pre-plateau) regime only") --
    found 2026-08-13: every caller previously passed `fit_window=(0,
    len(radii))`, the FULL trajectory, which contradicts this line.

    Trims a flat LEAD-IN (radius stuck at its initial value -- a genuine
    "quiet period" before the pulse spreads past the source node, not
    saturation) and a flat TRAIL (radius stuck at its final/saturated
    value) from the two ends of `radii`, returning everything in between
    -- the actual rising regime, however it is shaped.

    Revised 2026-08-13 (a second time, investigating the [A9] sweep's own
    `v_eff` being suspiciously uniform ~20.0 across all 25 points): the
    prior "longest strictly-increasing run" version degenerates to a
    2-point window on real hop-count-quantized data, which is a
    STAIRCASE (radius holds an integer value for many steps, then jumps)
    -- no run of MORE than 2 points is ever strictly increasing in a
    staircase, so that version always returned the single largest jump,
    mechanically forcing `v_eff = 1/dt` regardless of the real spreading
    rate (confirmed: transition indices `[16, 42, 73]` were bit-identical
    for K=10 and K=200 -- a 20x difference in adaptation budget -- because
    both runs picked the exact same single first jump, not because the
    real dynamics were identical). Trimming lead-in/trail-out instead
    keeps every intermediate plateau's timing information, which is
    exactly what a staircase's average velocity needs.

    Clamped to a minimum window of 2 points so `fit_effective_velocity`'s
    `scipy.stats.linregress` always has enough data for a line -- an
    entirely flat trajectory (`radii[0] == radii[-1]`) has no real
    unsaturated regime to report, so the 2-point floor from index 0 is a
    degenerate fallback, not a meaningful velocity estimate.
    """
    n = len(radii)
    if n < 2:
        return (0, n)
    if radii[0] == radii[-1]:
        return (0, min(2, n))

    lead_in_end = 0
    while lead_in_end + 1 < n and radii[lead_in_end + 1] == radii[0]:
        lead_in_end += 1
    start = lead_in_end

    trail_start = n - 1
    while trail_start - 1 >= 0 and radii[trail_start - 1] == radii[-1]:
        trail_start -= 1
    end = trail_start + 1

    if end - start < 2:
        end = min(start + 2, n)
    return (start, end)


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
