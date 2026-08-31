"""Tests for reporting and deleting finished task branches."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_abandoned_record,
    create_completed_record,
    write_record,
)

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    for title in ("Done task", "Open task", "Abandoned task"):
        assert main(["open", "--title", title, "--scope", "src/"]) == 0
    head = _commit(repo, "journal tasks")
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "0.1.0", head))
    write_record(
        journal,
        "CR-003",
        create_abandoned_record("CR-003", "0.1.0", "no longer needed"),
    )
    _commit(repo, "close tasks")
    return repo


def _local_branches(repo: Path) -> set[str]:
    output = _git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    return set(output.splitlines())


def test_report_lists_only_done_merged_branch_and_deletes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    for branch in (
        "feat/CR-001-merged",
        "feat/CR-002-open",
        "feat/CR-003-abandoned",
        "feat/CR-999-unknown",
    ):
        _git(repo, "branch", branch)
    _git(repo, "switch", "--quiet", "-c", "feat/CR-001-unmerged")
    _commit(repo, "unmerged work")
    _git(repo, "switch", "--quiet", "master")
    before = _local_branches(repo)
    capsys.readouterr()

    assert main(["prune-branches"]) == 0

    output = capsys.readouterr()
    assert "eligible: feat/CR-001-merged" in output.out
    assert "skipped: feat/CR-001-unmerged" in output.out
    assert "not merged" in output.out
    assert "skipped: feat/CR-002-open (task CR-002 is open)" in output.out
    assert "skipped: feat/CR-003-abandoned (task CR-003 is abandoned)" in output.out
    assert "skipped: feat/CR-999-unknown (task CR-999 is unknown)" in output.out
    assert output.err == ""
    assert _local_branches(repo) == before


def test_delete_removes_exactly_the_reported_branches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-one")
    _git(repo, "branch", "completion/CR-001-two")
    _git(repo, "branch", "feat/CR-002-open")
    remote_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/CR-001-backup", remote_sha)
    capsys.readouterr()

    assert main(["prune-branches", "--delete"]) == 0

    output = capsys.readouterr()
    assert "deleted: feat/CR-001-one" in output.out
    assert "deleted: completion/CR-001-two" in output.out
    assert "deleted: feat/CR-002-open" not in output.out
    assert "feat/CR-001-one" not in _local_branches(repo)
    assert "completion/CR-001-two" not in _local_branches(repo)
    assert "feat/CR-002-open" in _local_branches(repo)
    assert _git(repo, "rev-parse", "refs/remotes/origin/CR-001-backup") == remote_sha


def test_current_branch_is_never_eligible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "switch", "--quiet", "-c", "feat/CR-001-current")
    capsys.readouterr()

    assert main(["prune-branches", "--delete"]) == 0

    output = capsys.readouterr().out
    assert "skipped: feat/CR-001-current (currently checked out)" in output
    assert "feat/CR-001-current" in _local_branches(repo)


def test_base_controls_containment_and_defaults_to_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "switch", "--quiet", "-c", "feat/CR-001-work")
    work = _commit(repo, "task work")
    _git(repo, "switch", "--quiet", "master")
    _git(repo, "branch", "integration", work)
    capsys.readouterr()

    assert main(["prune-branches"]) == 0
    assert "skipped: feat/CR-001-work" in capsys.readouterr().out

    assert main(["prune-branches", "--base", "integration"]) == 0
    assert "eligible: feat/CR-001-work" in capsys.readouterr().out


def test_a_refusal_from_git_is_reported_and_the_branch_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """git's own check is the second of two independent guards, so it is kept.

    ``--base`` can honestly name a ref that ``git branch -d`` does not judge
    against. When the two disagree the operator is told, and nothing is forced.
    """

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-work")
    _git(repo, "switch", "--quiet", "feat/CR-001-work")
    unmerged = _commit(repo, "work that master does not contain")
    _git(repo, "switch", "--quiet", "master")
    # The branch is contained in itself, so the report finds it eligible; git,
    # judging against the checked-out master, refuses to delete it.
    assert main(["prune-branches", "--base", unmerged, "--delete"]) == 1

    captured = capsys.readouterr()
    assert "eligible: feat/CR-001-work" in captured.out
    assert "refused: feat/CR-001-work" in captured.err
    assert "deleted:" not in captured.out
    assert "feat/CR-001-work" in _local_branches(repo)


def test_a_branch_of_an_unknown_task_is_skipped_not_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Absence is asked of the filesystem, never read out of an error message."""

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-404-never-opened")

    assert main(["prune-branches"]) == 0

    captured = capsys.readouterr()
    assert "skipped: feat/CR-404-never-opened (task CR-404 is unknown)" in captured.out
    assert "feat/CR-404-never-opened" in _local_branches(repo)
