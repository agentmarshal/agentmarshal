"""Tests for ``templates/journal-transaction.sh``.

The template is the shipped form of the journal-transaction pattern:
from the default branch, one task's journal directory per transaction,
everything else under the journal listed and left as it is. These tests
run the script against temporary git repositories — a bare remote and a
clone of it — so the staging, the refusals and the push are checked
against real git behaviour, not a description of it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "templates" / "journal-transaction.sh"
TASKS = ".agentmarshal/journal/tasks"


def _git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _git_out(cwd: Path, *arguments: str) -> str:
    return _git(cwd, *arguments).stdout.strip()


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    """A bare remote and a work clone of it, on the remote's default branch.

    The clone — rather than a ``remote add`` — is what leaves
    ``refs/remotes/origin/HEAD`` in the work repository, which is where
    the script reads the default branch's name. Git identity is
    configured inside the temporary repositories, so the test passes with
    no global git configuration at all.
    """

    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-b", "master", str(remote))

    seed = tmp_path / "seed"
    _git(tmp_path, "init", "--quiet", "-b", "master", str(seed))
    _git(seed, "config", "user.name", "Adopter")
    _git(seed, "config", "user.email", "adopter@test.invalid")
    (seed / "README.md").write_text("seed\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "--quiet", "-m", "seed")
    _git(seed, "remote", "add", "origin", str(remote))
    _git(seed, "push", "--quiet", "--set-upstream", "origin", "master")

    work = tmp_path / "work"
    _git(tmp_path, "clone", "--quiet", str(remote), str(work))
    _git(work, "config", "user.name", "Adopter")
    _git(work, "config", "user.email", "adopter@test.invalid")
    return work, remote


def _record(repo: Path, task: str, name: str = "01JTEST00RECORD000000000.json") -> Path:
    """An uncommitted record under the task's journal directory."""

    record = repo / TASKS / task / "records" / name
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("{}\n", encoding="utf-8")
    return record


def _message_file(tmp_path: Path) -> Path:
    message = tmp_path / "message.txt"
    message.write_text("journal transaction\n", encoding="utf-8")
    return message


def _run(
    repo: Path, *arguments: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the template in ``repo`` with a clean, identity-free environment.

    ``AGENTMARSHAL_*`` and ``GIT_*`` are stripped, then the global and
    system git configurations are switched off — the repositories' own
    local configuration is the only git identity available, exactly the
    condition CI runs the suite in.
    """

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("AGENTMARSHAL_", "GIT_"))
    }
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    if env_extra:
        env.update(env_extra)
    # Executed by its own path, not through `sh`: the contract's invocation
    # is direct, so the run itself asserts the template ships executable.
    return subprocess.run(
        [str(SCRIPT), *arguments],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="the template is POSIX shell")
def test_the_transaction_takes_only_its_own_tasks_journal_directory(
    tmp_path: Path,
) -> None:
    """CR-207: run for one task, the commit holds only that task's journal
    directory; another task's uncommitted record is listed on the output
    and left unstaged, and the branch — named for the task — is pushed to
    the default remote, origin."""

    work, remote = _repository(tmp_path)
    _record(work, "CR-001")
    other = _record(work, "CR-002")
    message = _message_file(tmp_path)

    result = _run(work, "CR-001", "add-greeting", str(message))

    assert result.returncode == 0, result.stdout + result.stderr
    committed = _git_out(
        work, "show", "--pretty=format:", "--name-only", "HEAD"
    ).splitlines()
    assert committed
    assert all(path.startswith(f"{TASKS}/CR-001/") for path in committed)
    assert "CR-002" in result.stdout + result.stderr
    assert "pull request" in (result.stdout + result.stderr).lower()
    # The other task's record is still untracked — listed, never staged.
    assert other.exists()
    assert "CR-002" not in _git_out(work, "diff", "--cached", "--name-only")
    assert (
        _git_out(work, "status", "--porcelain", "-uall", "--", f"{TASKS}/CR-002")
        == f"?? {TASKS}/CR-002/records/01JTEST00RECORD000000000.json"
    )
    # The branch carrying the task id was pushed to origin.
    head = _git_out(work, "rev-parse", "HEAD")
    remote_branch = _git_out(
        remote, "rev-parse", "refs/heads/journal/CR-001-add-greeting"
    )
    assert remote_branch == head


@pytest.mark.skipif(sys.platform == "win32", reason="the template is POSIX shell")
def test_the_push_goes_to_the_remote_am_remote_names(tmp_path: Path) -> None:
    """CR-207: with AM_REMOTE set, the branch is pushed to the named
    remote — and the default branch is read from that remote's HEAD too."""

    work, remote = _repository(tmp_path)
    _git(work, "remote", "add", "upstream", str(remote))
    _git(work, "fetch", "--quiet", "upstream")
    _git(work, "remote", "set-head", "upstream", "--auto")
    _record(work, "CR-007")
    message = _message_file(tmp_path)

    result = _run(
        work, "CR-007", "txn", str(message), env_extra={"AM_REMOTE": "upstream"}
    )

    assert result.returncode == 0, result.stdout + result.stderr
    head = _git_out(work, "rev-parse", "HEAD")
    assert _git_out(remote, "rev-parse", "refs/heads/journal/CR-007-txn") == head
    # Pushed through `upstream`, so no `origin/` tracking ref exists.
    assert (
        subprocess.run(
            [
                "git",
                "rev-parse",
                "--verify",
                "refs/remotes/origin/journal/CR-007-txn",
            ],
            cwd=work,
            capture_output=True,
        ).returncode
        != 0
    )


@pytest.mark.skipif(sys.platform == "win32", reason="the template is POSIX shell")
def test_refusals_stage_nothing_and_name_the_reason(tmp_path: Path) -> None:
    """CR-207: a task id that is not CR-<n>, a checkout off the default
    branch and a task directory with no change are each refused by name,
    staging nothing and leaving the checkout where it was."""

    work, _ = _repository(tmp_path)
    _record(work, "CR-001")
    message = _message_file(tmp_path)

    def refused(*arguments: str) -> subprocess.CompletedProcess[str]:
        branch = _git_out(work, "branch", "--show-current")
        result = _run(work, *arguments)
        assert result.returncode != 0
        assert "journal-transaction:" in result.stderr
        assert _git_out(work, "diff", "--cached", "--name-only") == ""
        assert _git_out(work, "branch", "--show-current") == branch
        return result

    for bad_id in ("feature-12", "CR-", "CR-x", "CR-1 2"):
        assert "CR-<n>" in refused(bad_id, "slug", str(message)).stderr

    _git(work, "switch", "-c", "wip")
    try:
        assert (
            "not on the default branch"
            in refused("CR-001", "slug", str(message)).stderr
        )
    finally:
        _git(work, "switch", "--quiet", "master")
        _git(work, "branch", "-qD", "wip")

    # CR-003 has no journal directory at all.
    assert "no journal directory" in refused("CR-003", "slug", str(message)).stderr

    # CR-004 has one, but it is committed and clean — nothing to commit.
    _record(work, "CR-004")
    _git(work, "add", f"{TASKS}/CR-004")
    _git(work, "commit", "--quiet", "-m", "seed CR-004")
    assert "no change" in refused("CR-004", "slug", str(message)).stderr


@pytest.mark.skipif(sys.platform == "win32", reason="the template is POSIX shell")
def test_a_renamed_foreign_record_is_listed_and_its_old_side_not_taken(
    tmp_path: Path,
) -> None:
    """CR-207: a foreign record renamed into this task's directory is
    still listed — a rename's old path is checked against the task's
    prefix too — and the deletion on the foreign side stays uncommitted,
    for the other task's own transaction."""

    work, _ = _repository(tmp_path)
    old = _record(work, "CR-002")
    _git(work, "add", f"{TASKS}/CR-002")
    _git(work, "commit", "--quiet", "-m", "seed CR-002")
    _record(work, "CR-001")
    old_rel = f"{TASKS}/CR-002/records/{old.name}"
    new_rel = f"{TASKS}/CR-001/records/taken.json"
    _git(work, "mv", old_rel, new_rel)
    message = _message_file(tmp_path)

    result = _run(work, "CR-001", "txn", str(message))

    assert result.returncode == 0, result.stdout + result.stderr
    # Both paths of the rename are reported — the old one is foreign.
    assert "not taken" in result.stdout
    assert old_rel in result.stdout
    assert new_rel in result.stdout
    # The task side was committed; the foreign deletion was not.
    committed = _git_out(
        work, "show", "--pretty=format:", "--name-only", "HEAD"
    ).splitlines()
    assert committed
    assert all(path.startswith(f"{TASKS}/CR-001/") for path in committed)
    assert old_rel not in committed
    assert _git_out(work, "ls-tree", "--name-only", "HEAD", "--", old_rel) == old_rel
    # The foreign deletion is left in the index, uncommitted.
    assert (
        _git_out(work, "status", "--porcelain", "--", f"{TASKS}/CR-002")
        == f"D  {old_rel}"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="the template is POSIX shell")
def test_a_foreign_path_mentioning_the_task_deeper_is_still_listed(
    tmp_path: Path,
) -> None:
    """CR-207: a foreign journal path that contains ``tasks/<task>/`` only
    deeper down — not as its prefix — is not this task's own: it is
    listed on the output and left untracked by the transaction."""

    work, _ = _repository(tmp_path)
    _record(work, "CR-001")
    deep_rel = ".agentmarshal/journal/archive/tasks/CR-001/copy.json"
    deep = work / deep_rel
    deep.parent.mkdir(parents=True)
    deep.write_text("{}\n", encoding="utf-8")
    message = _message_file(tmp_path)

    result = _run(work, "CR-001", "txn", str(message))

    assert result.returncode == 0, result.stdout + result.stderr
    assert deep_rel in result.stdout
    committed = _git_out(
        work, "show", "--pretty=format:", "--name-only", "HEAD"
    ).splitlines()
    assert committed
    assert all(path.startswith(f"{TASKS}/CR-001/") for path in committed)
    assert deep_rel not in committed
    assert (
        _git_out(work, "status", "--porcelain", "-uall", "--", deep_rel)
        == f"?? {deep_rel}"
    )
