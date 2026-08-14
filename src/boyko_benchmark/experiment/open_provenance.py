"""Phase 11 T10 (ТЗ §22, §26): full provenance tuple for an open-system
pilot run -- extends `experiment/provenance.py`'s `EnvironmentProvenance`
(reused, not duplicated) with the fields ТЗ §26 additionally requires:
`dirty_flag`, `config_hash`, `timestamp`, BLAS backend, CPU thread count,
and the 4 independent seed spaces ТЗ §8 requires (`graph_seed`,
`initial_state_seed`, `noise_seed`, `control_seed`).

"Scientific result on dirty=True is not a frozen production result"
(ТЗ §26) -- `dirty_flag` is recorded, never silently dropped or ignored,
so a caller can enforce that rule downstream.
"""

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from boyko_benchmark.experiment.provenance import (
    EnvironmentProvenance,
    collect_environment_provenance,
)


@dataclass(frozen=True)
class OpenPilotProvenance:
    environment: EnvironmentProvenance
    dirty_flag: bool
    config_hash: str
    timestamp: str
    blas_backend: str
    cpu_thread_count: int
    graph_seed: int | None
    initial_state_seed: int | None
    noise_seed: int | None
    control_seed: int | None


def _collect_dirty_flag(repo_path: str | None = None) -> bool:
    """True if the working tree has uncommitted changes (`git status
    --porcelain` non-empty), or if this cannot be determined (fail
    closed -- an unknown-cleanliness run is treated as dirty, never
    silently assumed clean)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return len(result.stdout.strip()) > 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return True


def _collect_blas_backend() -> str:
    """Best-effort BLAS backend name from numpy's build config -- numpy
    version differences in how this is exposed mean this is genuinely
    best-effort, never raises."""
    try:
        import numpy

        config = numpy.show_config(mode="dicts")
        blas = config.get("Build Dependencies", {}).get("blas", {})
        name = blas.get("name")
        return str(name) if name else "UNKNOWN"
    except Exception:  # noqa: BLE001 -- provenance collection must never crash the run
        return "UNKNOWN"


def compute_config_hash(config: dict[str, Any]) -> str:
    """Deterministic hash of a config dict -- sorted-key JSON, so field
    order never changes the hash, only content does."""
    canonical = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect_open_pilot_provenance(
    config: dict[str, Any],
    graph_seed: int | None,
    initial_state_seed: int | None,
    noise_seed: int | None,
    control_seed: int | None,
    repo_path: str | None = None,
) -> OpenPilotProvenance:
    return OpenPilotProvenance(
        environment=collect_environment_provenance(repo_path),
        dirty_flag=_collect_dirty_flag(repo_path),
        config_hash=compute_config_hash(config),
        timestamp=datetime.now(UTC).isoformat(),
        blas_backend=_collect_blas_backend(),
        cpu_thread_count=os.cpu_count() or 0,
        graph_seed=graph_seed,
        initial_state_seed=initial_state_seed,
        noise_seed=noise_seed,
        control_seed=control_seed,
    )


def provenance_to_dict(provenance: OpenPilotProvenance) -> dict[str, Any]:
    """Flat dict for JSONL persistence (ТЗ §27) -- environment sub-fields
    flattened to the top level rather than nested, for a simpler schema
    in the incremental output file."""
    result = asdict(provenance)
    environment = result.pop("environment")
    result.update(environment)
    return result
