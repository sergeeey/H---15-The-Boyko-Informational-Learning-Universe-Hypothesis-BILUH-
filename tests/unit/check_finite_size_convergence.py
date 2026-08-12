"""Unit tests for G1's finite-size convergence criterion
(falsification_gates.md: 'its estimate at the largest N tested falls
within the 95% CI of its estimate at the second-largest N')."""

from boyko_benchmark.statistics.finite_size_scaling import (
    SizeEstimate,
    check_finite_size_convergence,
)


def test_convergence_holds_when_largest_n_mean_is_inside_second_largest_ci() -> None:
    estimates = [
        SizeEstimate(size=64, mean=1.5, ci_95=(1.3, 1.7)),
        SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
        SizeEstimate(size=512, mean=2.05, ci_95=(1.9, 2.2)),
    ]

    assert check_finite_size_convergence(estimates) is True


def test_convergence_fails_when_largest_n_mean_drifts_outside_second_largest_ci() -> None:
    estimates = [
        SizeEstimate(size=64, mean=1.5, ci_95=(1.3, 1.7)),
        SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
        SizeEstimate(size=512, mean=3.0, ci_95=(2.8, 3.2)),
    ]

    assert check_finite_size_convergence(estimates) is False


def test_convergence_is_order_independent_and_uses_only_two_largest_sizes() -> None:
    """Passing estimates out of size order, and including a smaller-N
    outlier that would fail convergence if mistakenly compared against,
    must not affect the result -- only the two LARGEST sizes matter."""
    out_of_order = [
        SizeEstimate(size=512, mean=2.05, ci_95=(1.9, 2.2)),
        SizeEstimate(size=64, mean=99.0, ci_95=(98.0, 100.0)),
        SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
    ]

    assert check_finite_size_convergence(out_of_order) is True


def test_convergence_boundary_is_inclusive() -> None:
    estimates = [
        SizeEstimate(size=216, mean=2.0, ci_95=(1.8, 2.2)),
        SizeEstimate(size=512, mean=2.2, ci_95=(2.0, 2.4)),
    ]

    assert check_finite_size_convergence(estimates) is True


def test_convergence_requires_at_least_two_sizes() -> None:
    estimates = [SizeEstimate(size=64, mean=1.5, ci_95=(1.3, 1.7))]

    try:
        check_finite_size_convergence(estimates)
        raise AssertionError("expected ValueError for fewer than two sizes")
    except ValueError:
        pass
