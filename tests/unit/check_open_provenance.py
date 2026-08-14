"""Phase 11 T10 (ТЗ §22, §26): provenance tuple tests."""

from boyko_benchmark.experiment.open_provenance import (
    collect_open_pilot_provenance,
    compute_config_hash,
    provenance_to_dict,
)


def test_t10_config_hash_is_deterministic_and_order_independent() -> None:
    config_a = {"K": 50, "eta": 0.1, "gamma": 0.1}
    config_b = {"eta": 0.1, "gamma": 0.1, "K": 50}  # same content, different key order

    assert compute_config_hash(config_a) == compute_config_hash(config_b)


def test_t10_config_hash_differs_for_different_configs() -> None:
    config_a = {"K": 50, "eta": 0.1}
    config_b = {"K": 100, "eta": 0.1}

    assert compute_config_hash(config_a) != compute_config_hash(config_b)


def test_t10_provenance_stores_full_seed_tuple_exactly() -> None:
    provenance = collect_open_pilot_provenance(
        config={"K": 50},
        graph_seed=1,
        initial_state_seed=2,
        noise_seed=3,
        control_seed=4,
    )

    assert provenance.graph_seed == 1
    assert provenance.initial_state_seed == 2
    assert provenance.noise_seed == 3
    assert provenance.control_seed == 4


def test_t10_provenance_records_git_state_never_crashes() -> None:
    """Provenance collection must never raise, even off a real repo --
    dirty_flag/git_commit_hash degrade gracefully (fail-closed to
    dirty=True / UNKNOWN-<reason>) rather than propagating an exception
    that would abort a real pilot run."""
    provenance = collect_open_pilot_provenance(
        config={}, graph_seed=None, initial_state_seed=None, noise_seed=None, control_seed=None
    )

    assert isinstance(provenance.dirty_flag, bool)
    assert isinstance(provenance.environment.git_commit_hash, str)
    assert len(provenance.environment.git_commit_hash) > 0


def test_t10_provenance_to_dict_flattens_environment_fields() -> None:
    provenance = collect_open_pilot_provenance(
        config={"K": 50}, graph_seed=1, initial_state_seed=2, noise_seed=3, control_seed=4
    )

    flat = provenance_to_dict(provenance)

    assert "git_commit_hash" in flat  # was nested under "environment"
    assert "environment" not in flat  # no longer nested
    assert flat["graph_seed"] == 1
    assert flat["config_hash"] == provenance.config_hash
