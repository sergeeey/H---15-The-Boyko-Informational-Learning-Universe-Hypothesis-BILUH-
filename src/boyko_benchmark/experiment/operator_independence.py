"""Operator-Independence Diagnostic (mathematical_contract.md Sec5.6,
required, mandatory report -- apparatus-trust infrastructure, NOT an 8th
experimental arm).

Corrected diagnostic (2nd skeptic pass, .claude/memory/decisions.md): a
FULL PARALLEL DYNAMICS RERUN, not a readout-only operator swap. The
superseded first version recomputed G1/G2/G4 under L on top of an
already-L_norm-shaped W(tau) -- since L = D^(1/2) L_norm D^(1/2) on the
same W, that swap stayed quiet almost always, giving false reassurance
exactly where it was needed. The corrected version drives BOTH the
propagation AND the Hebbian weight-shaping itself with H := L
(combinatorial), from the same (M(0), W(0), psi(0)) as Active, producing
an independently-shaped W'(tau) whose own FSS behavior is compared to
Active's (by the caller -- this module only produces the rerun).
"""

from boyko_benchmark.arms.shared_initialization import SharedInitialization
from boyko_benchmark.dynamics.adaptive import HebbianAdaptation
from boyko_benchmark.experiment.runner import (
    AdaptiveRunResult,
    localized_psi0,
    run_adaptive_dynamics,
)
from boyko_benchmark.graphs.weights import combinatorial_laplacian


def run_operator_independence_diagnostic(
    shared_init: SharedInitialization, eta: float, dt: float, k: int, dtau_steps: int
) -> AdaptiveRunResult:
    """H := L drives both the fast dynamics and the Hebbian correlation
    signal that shapes W'(tau) -- exactly Active's own loop
    (`experiment.arms_runner.run_arm_active`) with only `hamiltonian_fn`
    swapped from `normalized_laplacian` to `combinatorial_laplacian`.

    Timescale caveat (Sec5.6, NOT resolved here): spec(L) is unbounded
    while spec(L_norm) is bounded in [0,2) -- using the same `dt`/`k` for
    this rerun as for Active means the K-step window covers a different
    amount of phase rotation under each operator. Confirming `k`
    corresponds to a comparable fraction of each operator's own
    characteristic timescale (or rescaling `dt` for this rerun) is a
    required check the CALLER must perform before interpreting a
    difference between this rerun and Active as an "operator effect" --
    this function does not attempt that rescaling itself, deliberately
    (no production data exists yet to calibrate it against)."""
    psi0 = localized_psi0(shared_init.graph.n_nodes, shared_init.source_nodes[0])
    return run_adaptive_dynamics(
        shared_init.graph,
        psi0,
        HebbianAdaptation(eta=eta),
        dt,
        k,
        dtau_steps,
        hamiltonian_fn=combinatorial_laplacian,
    )
