"""Gate-A verdict machine (falsification_gates.md).

Six criteria G1-G6, evaluated per arm ACROSS THE FULL FSS GRID -- never
from a single N or seed. This is the ONLY module authorized to compute or
emit a Stage-1 verdict (falsification_gates.md's own mandate).

Gate B (physical spacetime) is explicitly out of scope -- nothing here
computes, implies, or names it.
"""

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.observables.propagation_front import PropagationFrontFit
from boyko_benchmark.statistics.cell_statistics import mcid_gate
from boyko_benchmark.statistics.finite_size_scaling import (
    LogarithmicFit,
    PowerLawFit,
    SizeEstimate,
    check_finite_size_convergence,
    fit_logarithmic,
    fit_power_law,
    power_law_beats_logarithmic,
)


class GateStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class G1Result:
    status: GateStatus
    converges: bool


def evaluate_g1(estimates: list[SizeEstimate]) -> G1Result:
    """G1: the largest-N d_s(t) plateau estimate falls within the
    second-largest-N's 95% CI (falsification_gates.md G1 row)."""
    converges = check_finite_size_convergence(estimates)
    return G1Result(status=GateStatus.PASS if converges else GateStatus.FAIL, converges=converges)


@dataclass(frozen=True)
class ExponentGateResult:
    status: GateStatus
    fit: PowerLawFit
    exponent_used: float


def evaluate_g2(
    sizes: NDArray[np.floating], gap_values: NDArray[np.floating]
) -> ExponentGateResult:
    """G2: gamma = -exponent (gap(N) ~ N^-gamma). PASS iff gamma>0 AND fit R^2>=0.9."""
    fit = fit_power_law(sizes, gap_values)
    gamma = -fit.exponent
    passed = gamma > 0 and fit.r_squared >= 0.9
    return ExponentGateResult(
        status=GateStatus.PASS if passed else GateStatus.FAIL, fit=fit, exponent_used=gamma
    )


def evaluate_g4(
    sizes: NDArray[np.floating], ipr_values: NDArray[np.floating]
) -> ExponentGateResult:
    """G4: eta = -exponent (IPR(N) ~ N^-eta). PASS iff eta>0 (bounded away
    from 0) AND fit R^2>=0.9."""
    fit = fit_power_law(sizes, ipr_values)
    eta = -fit.exponent
    passed = eta > 0 and fit.r_squared >= 0.9
    return ExponentGateResult(
        status=GateStatus.PASS if passed else GateStatus.FAIL, fit=fit, exponent_used=eta
    )


@dataclass(frozen=True)
class G3Result:
    status: GateStatus
    power_fit: PowerLawFit
    log_fit: LogarithmicFit
    delta: float


def evaluate_g3(
    sizes: NDArray[np.floating], resistance_diameters: NDArray[np.floating]
) -> G3Result:
    """G3: delta = +exponent (resistance_diameter(N) ~ N^delta, growth).
    PASS iff delta>0 AND the power-law fit beats the logarithmic
    alternative (`[A23]`)."""
    power_fit = fit_power_law(sizes, resistance_diameters)
    log_fit = fit_logarithmic(sizes, resistance_diameters)
    delta = power_fit.exponent
    passed = delta > 0 and power_law_beats_logarithmic(power_fit, log_fit)
    return G3Result(
        status=GateStatus.PASS if passed else GateStatus.FAIL,
        power_fit=power_fit,
        log_fit=log_fit,
        delta=delta,
    )


@dataclass(frozen=True)
class G5Result:
    status: GateStatus
    fit: PropagationFrontFit


def evaluate_g5(fit: PropagationFrontFit) -> G5Result:
    """G5: R^2>=0.9 over the fit's own declared window, finite positive v_eff."""
    passed = fit.r_squared >= 0.9 and fit.v_eff > 0 and np.isfinite(fit.v_eff)
    return G5Result(status=GateStatus.PASS if passed else GateStatus.FAIL, fit=fit)


@dataclass(frozen=True)
class G6Cell:
    observable: str
    comparator: str
    cleared_mcid: bool


class G6Tier(StrEnum):
    STRONG = "G6_STRONG"
    PARTIAL = "G6_PARTIAL"
    FAIL = "G6_FAIL"


@dataclass(frozen=True)
class G6Result:
    cells: tuple[G6Cell, ...]
    n_cleared: int
    tier: G6Tier


def evaluate_g6(
    samples_by_cell: dict[tuple[str, str], tuple[NDArray[np.floating], NDArray[np.floating]]],
) -> G6Result:
    """G6 Tiering (falsification_gates.md): `samples_by_cell` maps
    `(observable_name, comparator_name)` to `(active_samples,
    comparator_samples)`. 15/15 cleared -> STRONG, >=10/15 -> PARTIAL
    (10 = 2/3 of 15, pre-registered), else FAIL."""
    cells = tuple(
        G6Cell(
            observable=observable,
            comparator=comparator,
            cleared_mcid=mcid_gate(active_samples, comparator_samples),
        )
        for (observable, comparator), (
            active_samples,
            comparator_samples,
        ) in samples_by_cell.items()
    )
    n_cleared = sum(1 for cell in cells if cell.cleared_mcid)
    if n_cleared == 15:
        tier = G6Tier.STRONG
    elif n_cleared >= 10:
        tier = G6Tier.PARTIAL
    else:
        tier = G6Tier.FAIL
    return G6Result(cells=cells, n_cleared=n_cleared, tier=tier)


class StageOneVerdict(StrEnum):
    SURVIVES = "SURVIVES_GEOMETRIC_PHASE_SCREEN"
    SURVIVES_PARTIAL = "SURVIVES_GEOMETRIC_PHASE_SCREEN_PARTIAL"
    FAILS = "FAILS_GEOMETRIC_PHASE_SCREEN"


def compute_verdict(
    g1: G1Result,
    g2: ExponentGateResult,
    g3: G3Result,
    g4: ExponentGateResult,
    g5: G5Result,
    g6: G6Result,
) -> StageOneVerdict:
    """Verdict Machine (falsification_gates.md): G1..G5 all PASS AND
    G6_STRONG -> SURVIVES; G1..G5 all PASS AND G6_PARTIAL ->
    SURVIVES_PARTIAL; otherwise FAILS. No fourth silent outcome."""
    all_pass = all(gate.status == GateStatus.PASS for gate in (g1, g2, g3, g4, g5))
    if all_pass and g6.tier == G6Tier.STRONG:
        return StageOneVerdict.SURVIVES
    if all_pass and g6.tier == G6Tier.PARTIAL:
        return StageOneVerdict.SURVIVES_PARTIAL
    return StageOneVerdict.FAILS
