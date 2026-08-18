"""`docs/v5_spec.md` Sec14: wiring check for `run_signal_diagnostic_
one_seed` -- small-scale (N=8 lattice), not the real N=512 campaign.
Confirms topology genuinely never changes (frozen, per `Identity
StatefulTopology`) and checkpoints land at the requested window counts.
"""

from boyko_benchmark.experiment.signal_diagnostic_gate import run_signal_diagnostic_one_seed
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice


def test_topology_never_changes_and_checkpoints_land_at_requested_windows() -> None:
    result = run_signal_diagnostic_one_seed(
        side_length=2,  # N=8
        damage_fraction=0.2,
        checkpoint_windows=(1, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=0,
        master_seed=11,
    )

    assert [cp.window_count for cp in result.checkpoints] == [1, 3]
    assert len(result.damaged_out) > 0
    for cp in result.checkpoints:
        assert cp.d == len(result.damaged_out)
        assert 0.0 <= cp.recall_at_d <= 1.0
        assert 0.0 <= cp.auprc <= 1.0
        assert cp.baseline_recall == cp.d / cp.n_candidates
        assert 0.0 < cp.baseline_auprc < 1.0


def test_frozen_topology_means_n_candidates_is_identical_across_checkpoints() -> None:
    """Since IdentityStatefulTopology never adds/removes edges, the
    candidate universe (non-adjacent pairs) must be IDENTICAL at every
    checkpoint for a given seed -- only C_ij values change."""
    result = run_signal_diagnostic_one_seed(
        side_length=2,
        damage_fraction=0.2,
        checkpoint_windows=(1, 2, 3),
        eta=0.1,
        dt=0.05,
        k=5,
        seed_index=0,
        master_seed=11,
    )

    n_candidates = {cp.n_candidates for cp in result.checkpoints}
    assert len(n_candidates) == 1

    # corrupt_lattice_edges is itself degree-preserving (removes D edges,
    # adds D different ones elsewhere) -- total edge COUNT is unchanged
    # by damage, verified directly here rather than assumed.
    graph = generate_periodic_cubic_lattice(2)
    total_pairs = graph.n_nodes * (graph.n_nodes - 1) // 2
    original_edges = int(graph.mask.sum()) // 2
    assert n_candidates.pop() == total_pairs - original_edges
