"""Phase 11 §13 calibration: detect_plateau against real geometric and
non-geometric reference curves, not just synthetic hand-derived arrays.
Numbers cross-checked via a background calibration script before writing
assertions (same discipline as every other observable this project).

Per ТЗ §13: "the detector must pass known geometry and reject obvious
false plateaus." MAJOR finding ([A36], docs/assumptions.md): this is a
genuine N-dependent resolving-power question, not just a detector-
tuning exercise --

- At N=64: 1D ring and 2D square lattice DO converge near their true
  dimensions. 3D cubic lattice does NOT converge -- and its raw d_s(t)
  curve is numerically almost indistinguishable from an Erdos-Renyi
  random graph's own curve at the same N/mean-degree. G1 (spectral
  dimension via heat kernel) simply lacks the resolving power to tell
  3D lattice geometry from a random graph at this small a scale --
  this is NOT a detect_plateau bug, thresholds cannot fix an observable
  that hasn't diverged yet at this N.
- At N=512 (this project's largest tested size): the SAME comparison
  cleanly resolves. Cubic lattice converges (d_s_hat=3.53, R^2=0.75, a
  real 3-point plateau near t=4.3-10) while Erdos-Renyi does NOT --
  its d_s(t) is still monotonically CLIMBING at t=10 (2.70 -> 5.27,
  no peak reached yet within the grid), the same "expander peak grows
  with N, no plateau" signature already found for Active
  (docs/assumptions.md [A30]).

Practical consequence: any G1 verdict from a pilot-scale run (N<=125)
is unreliable not just for statistical-power reasons but because the
OBSERVABLE ITSELF has not yet separated geometric from non-geometric
graphs at that scale. G1 needs N>=512 (in this project's tested range)
to mean anything as a discriminator.
"""

import numpy as np

from boyko_benchmark.graphs.generators import generate_erdos_renyi
from boyko_benchmark.graphs.lattice import (
    generate_periodic_cubic_lattice,
    generate_periodic_ring,
    generate_periodic_square_lattice,
)
from boyko_benchmark.graphs.weights import normalized_laplacian
from boyko_benchmark.observables.spectral_dimension import detect_plateau, spectral_dimension

_T_VALUES = np.geomspace(0.1, 10.0, num=12)


def test_calibration_1d_ring_converges_near_true_dimension_one() -> None:
    ring = generate_periodic_ring(64)
    d_s = spectral_dimension(normalized_laplacian(ring), _T_VALUES)

    result = detect_plateau(_T_VALUES, d_s)

    assert result.converged is True
    assert abs(result.d_s_hat - 1.0) < 0.3  # target d_s~1, [A36] provisional tolerance


def test_calibration_2d_square_converges_near_true_dimension_two() -> None:
    square = generate_periodic_square_lattice(8)  # 8^2 = 64
    d_s = spectral_dimension(normalized_laplacian(square), _T_VALUES)

    result = detect_plateau(_T_VALUES, d_s)

    assert result.converged is True
    assert abs(result.d_s_hat - 2.0) < 0.5  # target d_s~2, [A36] provisional tolerance


def test_calibration_3d_cubic_and_random_graph_indistinguishable_at_n64() -> None:
    """[A36]: documents the N=64 resolving-power gap explicitly, as a
    real finding, not a silent failure -- both the cubic lattice AND an
    Erdos-Renyi random graph fail to converge at this N, confirming
    neither the lattice nor the random graph has a resolvable plateau
    at this scale (not that the detector picked the wrong one)."""
    cubic = generate_periodic_cubic_lattice(4)  # 4^3 = 64
    d_s_cubic = spectral_dimension(normalized_laplacian(cubic), _T_VALUES)
    result_cubic = detect_plateau(_T_VALUES, d_s_cubic)

    rng = np.random.default_rng(2026)
    er = generate_erdos_renyi(64, 64 * 6 // 2, rng)
    d_s_er = spectral_dimension(normalized_laplacian(er), _T_VALUES)
    result_er = detect_plateau(_T_VALUES, d_s_er)

    assert result_cubic.converged is False
    assert result_er.converged is False


def test_calibration_3d_cubic_and_random_graph_resolve_cleanly_at_n512() -> None:
    """The decisive calibration result: at N=512, G1 DOES discriminate
    real 3D geometry from a random graph -- cubic lattice converges near
    its true dimension 3, Erdos-Renyi does not (still climbing at
    t=10, the same expander signature [A30] already documented for
    Active). This is the "pass known geometry, reject obvious false
    plateau" requirement (ТЗ §13) satisfied together, at the N where the
    observable has actually separated the two cases."""
    cubic = generate_periodic_cubic_lattice(8)  # 8^3 = 512
    d_s_cubic = spectral_dimension(normalized_laplacian(cubic), _T_VALUES)
    result_cubic = detect_plateau(_T_VALUES, d_s_cubic)

    rng = np.random.default_rng(2027)
    er = generate_erdos_renyi(512, 512 * 6 // 2, rng)
    d_s_er = spectral_dimension(normalized_laplacian(er), _T_VALUES)
    result_er = detect_plateau(_T_VALUES, d_s_er)

    assert result_cubic.converged is True
    assert abs(result_cubic.d_s_hat - 3.0) < 1.0  # target d_s~3, [A36] provisional tolerance
    assert result_er.converged is False
