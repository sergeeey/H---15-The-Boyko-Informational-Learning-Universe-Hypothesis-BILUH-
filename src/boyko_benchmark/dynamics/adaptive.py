"""Adaptation-rule interfaces and rules (mathematical_contract.md Sec3, [A20]).

Terminology lock: `adaptive Hebbian meta-dynamics`, never `learning` -- no
objective functional L(W, psi) is defined here or proven to be what these
rules descend (Correction 2, [A3]).
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.types import WeightedGraph


@dataclass(frozen=True)
class StateTrajectory:
    """K+1 recorded fast-dynamics snapshots: psi at t=0, dt, ..., K*dt.

    [A20]: the time-averaged quantities used by the adaptation rules below
    average over ALL K+1 snapshots stored here, including t=0.
    """

    states: NDArray[np.complexfloating]  # shape (K+1, N)


class AdaptationRule(Protocol):
    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph: ...


def _time_averaged_correlation(trajectory: StateTrajectory) -> NDArray[np.floating]:
    """<Re(psi_i* psi_j)>_K over all recorded snapshots [A20].

    correlation[i, i] == <Re(psi_i* psi_i)>_K == <|psi_i|^2>_K exactly,
    since psi_i* psi_i is already real -- the diagonal doubles as the
    time-averaged density used by the Oja decay term and AlternativeObjective.
    """
    states = trajectory.states
    result: NDArray[np.floating] = np.real(np.conj(states)[:, :, None] * states[:, None, :]).mean(
        axis=0
    )
    return result


def _time_averaged_density(trajectory: StateTrajectory) -> NDArray[np.floating]:
    """<p_i>_K -- linear time-average, for the classical carrier's decay
    term ONLY. NOT interchangeable with the correlation matrix's diagonal:
    <p_i>_K != <p_i^2>_K in general. This differs from the quantum case
    specifically because psi is an amplitude (|psi_i|^2 is a DERIVED
    density, coinciding with the correlation diagonal), while classical p
    IS already the density -- squaring it again (what the diagonal would
    give) is a different, wrong quantity. Self-caught by a failing
    hand-derived test, not by inspection -- see
    .claude/memory/decisions.md."""
    result: NDArray[np.floating] = np.real(trajectory.states).mean(axis=0)
    return result


def _masked_nonnegative(
    raw_weights: NDArray[np.floating], mask: NDArray[np.bool_]
) -> NDArray[np.floating]:
    """Enforce the two invariants any update must preserve: weight only
    where the topology mask allows (Milestone 3 critical requirement,
    [A5]), and never negative (Milestone 1)."""
    masked = np.where(mask, raw_weights, 0.0)
    result: NDArray[np.floating] = np.maximum(masked, 0.0)
    return result


class NoAdaptation:
    """Frozen arm: weights never change (Milestone 3 critical requirement)."""

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        return graph


class HebbianAdaptation:
    """Oja-normalized Hebbian rule ([A3], revised 2026-08-11 skeptic pass 2):

    dW_ij/dtau = eta * (<Re(psi_i* psi_j)>_K - W_ij * (<|psi_i|^2>_K + <|psi_j|^2>_K)/2)
    """

    def __init__(self, eta: float) -> None:
        self._eta = eta

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        correlation = _time_averaged_correlation(trajectory)
        density = np.diagonal(correlation)
        decay_term = graph.weights * (density[:, None] + density[None, :]) / 2.0
        raw_delta = self._eta * dtau * (correlation - decay_term)
        new_weights = _masked_nonnegative(graph.weights + raw_delta, graph.mask)
        return WeightedGraph(mask=graph.mask, weights=new_weights)


def _shuffle_edge_correlations(
    correlation: NDArray[np.floating], mask: NDArray[np.bool_], rng: np.random.Generator
) -> NDArray[np.floating]:
    """H0 secondary-control helper (`[A31]`, docs/assumptions.md, proposed
    2026-08-13 external red-team review): permutes the off-diagonal
    correlation values across the graph's existing edges, preserving the
    multiset of values but destroying the correspondence between "which
    pair correlated" and "which edge gets it." Non-edge positions and the
    diagonal are left at 0.0 -- density (the diagonal) is a per-node
    quantity, deliberately not part of this edge-level shuffle."""
    n_nodes = correlation.shape[0]
    shuffled = np.zeros((n_nodes, n_nodes))
    edge_i, edge_j = np.nonzero(np.triu(mask, k=1))
    values = correlation[edge_i, edge_j]
    permuted_values = rng.permutation(values)
    shuffled[edge_i, edge_j] = permuted_values
    shuffled[edge_j, edge_i] = permuted_values
    return shuffled


class CorrelationShuffleAdaptation:
    """H0 secondary control (`[A31]`): identical Oja-normalized update to
    `HebbianAdaptation`, except the off-diagonal correlation term is
    shuffled across existing edges (`_shuffle_edge_correlations`) before
    being applied. Tests H1 ("structured correlations cause geometric
    organization") against H0 ("any reinforcement with the same
    correlation-magnitude distribution suffices, regardless of which pair
    correlated"). Not yet wired into `config.py`'s `Arm` enum as an 8th
    experimental arm -- see `[A31]`'s entry in `assumptions.md` for the
    documented next step.
    """

    def __init__(self, eta: float, rng: np.random.Generator) -> None:
        self._eta = eta
        self._rng = rng

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        correlation = _time_averaged_correlation(trajectory)
        shuffled_correlation = _shuffle_edge_correlations(correlation, graph.mask, self._rng)
        density = np.diagonal(correlation)
        decay_term = graph.weights * (density[:, None] + density[None, :]) / 2.0
        raw_delta = self._eta * dtau * (shuffled_correlation - decay_term)
        new_weights = _masked_nonnegative(graph.weights + raw_delta, graph.mask)
        return WeightedGraph(mask=graph.mask, weights=new_weights)


class AntiHebbianAdaptation:
    """[A3]: dW_ij/dtau = -eta * <Re(psi_i* psi_j)>_K -- deliberately no
    Oja term. Its own fixed point (decay toward the non-negativity floor)
    is a different, already-bounded pathology -- monitor via
    mean(W) < 0.1*mean(W(0)), don't "fix" it with growth-restoring
    normalization (mathematical_contract.md Sec3.2)."""

    def __init__(self, eta: float) -> None:
        self._eta = eta

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        correlation = _time_averaged_correlation(trajectory)
        raw_delta = -self._eta * dtau * correlation
        new_weights = _masked_nonnegative(graph.weights + raw_delta, graph.mask)
        return WeightedGraph(mask=graph.mask, weights=new_weights)


class AlternativeObjective:
    """[A4]: dW_ij/dtau = eta * (<|psi_i|^2>_K + <|psi_j|^2>_K)/2 --
    local-density-driven reinforcement, orthogonal to Hebbian's
    correlation-driven mechanism (ignores phase relationship entirely)."""

    def __init__(self, eta: float) -> None:
        self._eta = eta

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        correlation = _time_averaged_correlation(trajectory)
        density = np.diagonal(correlation)
        raw_delta = self._eta * dtau * (density[:, None] + density[None, :]) / 2.0
        new_weights = _masked_nonnegative(graph.weights + raw_delta, graph.mask)
        return WeightedGraph(mask=graph.mask, weights=new_weights)


class ClassicalHebbianAdaptation:
    """[A18], Arm CD only: dW_ij/dtau = eta * (<p_i*p_j>_K - W_ij*(<p_i>_K + <p_j>_K)/2).

    **Not** a HebbianAdaptation subclass, despite the superficially
    identical formula shape -- self-caught bug (2026-08-12, see
    .claude/memory/decisions.md): the quantum rule's "diagonal of the
    correlation matrix equals density" shortcut (<Re(psi_i* psi_i)>_K ==
    <|psi_i|^2>_K) does not transfer to the classical carrier, where p_i
    IS already the density, not an amplitude whose square gives density.
    A first draft subclassed HebbianAdaptation unchanged; it silently
    computed <p_i^2>_K instead of <p_i>_K for the decay term, caught by a
    hand-derived test failing (0.5125 vs the expected 0.5), not by
    inspection. The growth term (<p_i*p_j>_K, off-diagonal) is unaffected
    and still uses `_time_averaged_correlation` -- only the decay term's
    density needed its own function.

    Fed a StateTrajectory built from the classical diffusion carrier's `p`
    (dynamics/classical.py), not the quantum `psi`. The resulting sign
    asymmetry vs. HebbianAdaptation on a quantum trajectory -- p_i*p_j is
    always non-negative, unlike Re(psi_i* psi_j) which can be negative --
    is the scientifically relevant difference this arm exists to expose.
    """

    def __init__(self, eta: float) -> None:
        self._eta = eta

    def update(
        self, graph: WeightedGraph, trajectory: StateTrajectory, dtau: float
    ) -> WeightedGraph:
        correlation = _time_averaged_correlation(trajectory)
        density = _time_averaged_density(trajectory)
        decay_term = graph.weights * (density[:, None] + density[None, :]) / 2.0
        raw_delta = self._eta * dtau * (correlation - decay_term)
        new_weights = _masked_nonnegative(graph.weights + raw_delta, graph.mask)
        return WeightedGraph(mask=graph.mask, weights=new_weights)
