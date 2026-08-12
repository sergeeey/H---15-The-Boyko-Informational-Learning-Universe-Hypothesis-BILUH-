"""Unit tests for environment provenance (CLAUDE.md Reproducibility).

The happy-path test is verified against the ACTUAL installed environment
and the ACTUAL repo state, not mocked -- [VERIFIED, this session]
`git log`/`git status` on this repo confirmed zero commits exist yet
("your current branch 'master' does not have any commits yet"), so
`collect_git_commit_hash` on this repo is expected -- and observed -- to
hit the graceful-degradation path.

The failure-path tests mock `subprocess.run` directly rather than relying
on an actual non-git directory: a first attempt used `tempfile.
TemporaryDirectory()` assuming it would be outside any repo, but git
searches PARENT directories for `.git`, and this machine's temp directory
resolves to a location whose ancestor (`C:\\Users\\serge`) IS itself a git
repo -- confirmed directly (`git rev-parse --show-toplevel` from inside a
fresh temp dir returned `C:/Users/serge`, not an error). That was a flawed
test assumption, not an implementation bug: `collect_git_commit_hash`
correctly returned a real hash because git legitimately found a real
repo. Mocking the subprocess call sidesteps filesystem topology entirely
and tests the actual branches this function is responsible for.
"""

from unittest.mock import patch

import networkx
import numpy
import scipy

from boyko_benchmark.experiment.provenance import (
    EnvironmentProvenance,
    collect_environment_provenance,
    collect_git_commit_hash,
)


def test_git_commit_hash_degrades_gracefully_on_this_repos_current_no_commit_state() -> None:
    result = collect_git_commit_hash()

    assert result.startswith("UNKNOWN-")


def test_git_commit_hash_degrades_gracefully_when_git_is_not_installed() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = collect_git_commit_hash(repo_path="irrelevant")

    assert result == "UNKNOWN-FileNotFoundError"


def test_git_commit_hash_degrades_gracefully_when_git_command_fails() -> None:
    import subprocess

    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(returncode=128, cmd=["git", "rev-parse", "HEAD"]),
    ):
        result = collect_git_commit_hash(repo_path="irrelevant")

    assert result == "UNKNOWN-CalledProcessError"


def test_environment_provenance_matches_actually_installed_versions() -> None:
    result = collect_environment_provenance()

    assert isinstance(result, EnvironmentProvenance)
    assert result.numpy_version == numpy.__version__
    assert result.scipy_version == scipy.__version__
    assert result.networkx_version == networkx.__version__
    assert len(result.os_platform) > 0
    assert result.git_commit_hash.startswith("UNKNOWN-")
