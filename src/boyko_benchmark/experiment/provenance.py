"""Environment provenance (CLAUDE.md Reproducibility section): git commit
hash, library versions, OS metadata. Independent of any single run's
scientific config/seeds (those are ExperimentConfig's/SeedManager's job)
-- this module answers "what code and library versions produced this
run," not "what scientific parameters did."
"""

import platform
import subprocess
from dataclasses import dataclass

import networkx
import numpy
import scipy


@dataclass(frozen=True)
class EnvironmentProvenance:
    git_commit_hash: str
    python_version: str
    numpy_version: str
    scipy_version: str
    networkx_version: str
    os_platform: str


def collect_git_commit_hash(repo_path: str | None = None) -> str:
    """Current commit hash of the repo at `repo_path` (or cwd), or an
    `UNKNOWN-<reason>` marker if it cannot be determined (git missing, no
    commits yet, not a repo). Never silently fabricate a hash -- an
    unreproducible run must be recorded as such, not hidden."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"UNKNOWN-{type(exc).__name__}"


def collect_environment_provenance(repo_path: str | None = None) -> EnvironmentProvenance:
    return EnvironmentProvenance(
        git_commit_hash=collect_git_commit_hash(repo_path),
        python_version=platform.python_version(),
        numpy_version=numpy.__version__,
        scipy_version=scipy.__version__,
        networkx_version=networkx.__version__,
        os_platform=platform.platform(),
    )
