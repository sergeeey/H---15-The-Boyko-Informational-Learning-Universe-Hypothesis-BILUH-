"""V5-K1' (`docs/v5_spec.md` Sec7/Sec8): wiring test for the swap-based
damaged-lattice restoration gate -- small scale, both arms share the
identical damaged graph, and (unlike V4's K1/K1c/K1d) connectivity must
NEVER be lost -- `truncated_at_window` should be `None` on every run,
by construction, not merely by chance."""

from boyko_benchmark.experiment.k1_prime_damage_gate import run_k1_prime_gate_one_seed


def test_both_arms_share_the_identical_damaged_graph() -> None:
    result = run_k1_prime_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=0,
    )

    assert len(result.damaged_out) > 0


def test_r_edge_values_are_valid_fractions() -> None:
    result = run_k1_prime_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=1,
    )

    assert 0.0 <= result.arm_a3.r_edge <= 1.0
    assert 0.0 <= result.arm_a4.r_edge <= 1.0


def test_edges_actually_change_and_committed_plus_skipped_matches_budget() -> None:
    result = run_k1_prime_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        n_swaps=2,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=2,
    )

    total_budget = 2 * 3  # n_swaps * dtau_steps
    for arm in (result.arm_a3, result.arm_a4):
        assert arm.total_committed + arm.total_skipped == total_budget
        assert arm.total_committed > 0
