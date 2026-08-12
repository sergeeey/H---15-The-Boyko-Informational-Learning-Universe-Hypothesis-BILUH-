"""Unit tests for environment provenance (CLAUDE.md Reproducibility).

The happy-path test is verified against the ACTUAL repo state, not
mocked or hardcoded -- and that state CHANGED mid-session: `git log`/
`git status` originally confirmed zero commits existed ("your current
branch 'master' does not have any commits yet"), so `collect_git_commit_
hash` was first verified against the graceful-degradation path. The user
then asked this session to commit the whole project (`git commit`,
producing a real root commit) -- which is exactly the kind of real-world
event `collect_git_commit_hash`'s happy path exists to handle, so the
test below was updated to check that path directly, cross-referenced
against `git rev-parse HEAD` itself (not a hardcoded hash, so it stays
valid across whatever commit is HEAD at test time) rather than continuing
to assert a now-false "no commits" premise.

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

import subprocess
from unittest.mock import patch

import networkx
import numpy
import scipy

from boyko_benchmark.experiment.provenance import (
    EnvironmentProvenance,
    collect_environment_provenance,
    collect_git_commit_hash,
)


def test_git_commit_hash_returns_the_real_head_now_that_this_repo_has_a_commit() -> None:
    """Cross-checked against `git rev-parse HEAD` directly (not a
    hardcoded hash) so this stays correct across future commits too."""
    expected = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    result = collect_git_commit_hash()

    assert result == expected
    assert len(result) == 40
    assert not result.startswith("UNKNOWN-")


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
    assert len(result.git_commit_hash) == 40  # this repo now has a real commit
