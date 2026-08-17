"""Phase 11 §21: OpenPilotConfig schema -- loads the real
configs/open_pilot.yaml (not a synthetic fixture) so a schema/config drift
is caught by the gate suite, not only by manually running the script."""

from pathlib import Path

from boyko_benchmark.dynamics.open_config import OpenPilotConfig

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "open_pilot.yaml"


def test_open_pilot_yaml_loads_and_validates() -> None:
    config = OpenPilotConfig.from_yaml(_CONFIG_PATH)

    assert config.sizes == [512, 1024]
    assert config.seeds_per_cell == 10
    assert config.open_dynamics.gamma_tilde_levels == [0.05]
    assert config.open_dynamics.omega_ref == 2.0


def test_gamma_values_scales_by_omega_ref() -> None:
    config = OpenPilotConfig.from_yaml(_CONFIG_PATH)

    gamma_values = config.open_dynamics.gamma_values()

    assert gamma_values == [0.05 * 2.0]
