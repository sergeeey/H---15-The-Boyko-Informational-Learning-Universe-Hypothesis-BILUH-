"""M2 (`docs/v4_spec.md` Sec7/Sec8 M2): wiring test for the K1 gate
orchestration -- A3 (`CorrelationScorer`) and A4 (`DistanceStratified
ShuffleScorer`) must run from the IDENTICAL damaged lattice (same seed
index -> same `corrupt_lattice_edges` call), so the comparison is paired,
not just two independent random runs. Small scale (side_length=3, N=27)
-- this is infrastructure verification, not the real M2 campaign (that
runs at spec scale, N=512, `experiment/run_k1_gate.py`)."""

from boyko_benchmark.experiment.k1_damage_gate import run_k1_gate_one_seed


def test_both_arms_share_the_identical_damaged_graph() -> None:
    result = run_k1_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        rho=0.2,
        m=1,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=0,
    )

    assert result.damaged_out_a3 == result.damaged_out_a4
    assert len(result.damaged_out_a3) > 0


def test_r_edge_values_are_valid_fractions() -> None:
    result = run_k1_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        rho=0.2,
        m=1,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=1,
    )

    assert 0.0 <= result.r_edge_a3 <= 1.0
    assert 0.0 <= result.r_edge_a4 <= 1.0
    assert 0.0 <= result.wrong_removal_a3 <= 1.0
    assert 0.0 <= result.wrong_removal_a4 <= 1.0


def test_different_seed_indices_produce_different_damage() -> None:
    result_a = run_k1_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        rho=0.2,
        m=1,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=0,
    )
    result_b = run_k1_gate_one_seed(
        side_length=3,
        damage_fraction=0.2,
        rho=0.2,
        m=1,
        eta=0.1,
        dt=0.05,
        k=5,
        dtau_steps=3,
        seed_index=5,
    )

    assert result_a.damaged_out_a3 != result_b.damaged_out_a3
