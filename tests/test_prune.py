"""Tests for reporting and deleting finished task branches and worktrees."""

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


def _worktree_paths(repo: Path) -> set[Path]:
    output = _git(repo, "worktree", "list", "--porcelain")
    return {
        Path(line.removeprefix("worktree "))
        for line in output.splitlines()
        if line.startswith("worktree ")
    }


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

    assert main(["prune"]) == 0

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

    assert main(["prune", "--delete"]) == 0

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

    assert main(["prune", "--delete"]) == 0

    output = capsys.readouterr().out
    assert "skipped: feat/CR-001-current (checked out in a worktree)" in output
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

    assert main(["prune"]) == 0
    assert "skipped: feat/CR-001-work" in capsys.readouterr().out

    assert main(["prune", "--base", "integration"]) == 0
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
    assert main(["prune", "--base", unmerged, "--delete"]) == 1

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

    assert main(["prune"]) == 0

    captured = capsys.readouterr()
    assert "skipped: feat/CR-404-never-opened (task CR-404 is unknown)" in captured.out
    assert "feat/CR-404-never-opened" in _local_branches(repo)


def test_a_branch_held_by_a_linked_worktree_is_never_eligible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Proposal 010 is about executor worktrees; a branch one holds is in use.

    ``%(HEAD)`` marks only this worktree's branch, so a branch checked out
    elsewhere would otherwise be offered for deletion.
    """

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-elsewhere")
    _git(
        repo,
        "worktree",
        "add",
        "--quiet",
        str(tmp_path / "wt"),
        "feat/CR-001-elsewhere",
    )

    assert main(["prune"]) == 0

    output = capsys.readouterr().out
    assert "skipped: feat/CR-001-elsewhere (checked out in a worktree)" in output
    assert "eligible: feat/CR-001-elsewhere" not in output


def test_worktree_report_requires_done_task_and_clean_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    worktrees: dict[str, Path] = {}
    for branch in (
        "feat/CR-001-clean",
        "feat/CR-001-dirty",
        "feat/CR-002-open",
        "feat/CR-003-abandoned",
        "feat/CR-999-unknown",
    ):
        path = tmp_path / branch.rsplit("-", 1)[-1]
        worktrees[branch] = path
        _git(repo, "worktree", "add", "--quiet", "-b", branch, str(path), "HEAD")
    (worktrees["feat/CR-001-dirty"] / "uncommitted.txt").write_text(
        "precious work\n", encoding="utf-8"
    )
    capsys.readouterr()

    assert main(["prune"]) == 0

    output = capsys.readouterr()
    assert "Branches:" in output.out
    assert "Worktrees:" in output.out
    assert (
        f"eligible: {worktrees['feat/CR-001-clean']} "
        "(branch feat/CR-001-clean; task CR-001 is done and clean)"
    ) in output.out
    assert f"skipped: {worktrees['feat/CR-001-dirty']}" in output.out
    assert "task CR-001 is done but worktree is dirty" in output.out
    assert "task CR-002 is open" in output.out
    assert "task CR-003 is abandoned" in output.out
    assert "task CR-999 is unknown" in output.out
    assert output.err == ""


def test_main_worktree_is_never_eligible(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "switch", "--quiet", "-c", "feat/CR-001-main")
    capsys.readouterr()

    assert main(["prune", "--delete"]) == 0

    output = capsys.readouterr().out
    assert f"skipped: {repo} (branch feat/CR-001-main; main worktree)" in output
    assert repo in _worktree_paths(repo)


def test_delete_removes_only_eligible_worktree_without_its_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    clean = tmp_path / "clean"
    dirty = tmp_path / "dirty"
    _git(repo, "worktree", "add", "--quiet", "-b", "feat/CR-001-clean", str(clean))
    _git(repo, "worktree", "add", "--quiet", "-b", "feat/CR-001-dirty", str(dirty))
    (dirty / "uncommitted.txt").write_text("keep me\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["prune", "--delete"]) == 0

    output = capsys.readouterr()
    assert f"removed worktree: {clean}" in output.out
    assert f"removed worktree: {dirty}" not in output.out
    assert clean not in _worktree_paths(repo)
    assert dirty in _worktree_paths(repo)
    assert "feat/CR-001-clean" in _local_branches(repo)


def test_git_worktree_removal_refusal_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    locked = tmp_path / "locked"
    _git(
        repo,
        "worktree",
        "add",
        "--quiet",
        "-b",
        "feat/CR-001-locked",
        str(locked),
    )
    _git(repo, "worktree", "lock", str(locked))
    capsys.readouterr()

    assert main(["prune", "--delete"]) == 1

    output = capsys.readouterr()
    assert f"eligible: {locked}" in output.out
    assert f"refused worktree: {locked}" in output.err
    assert locked in _worktree_paths(repo)


def test_the_main_worktree_is_never_offered_even_from_inside_a_linked_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """git lists the main worktree first; the invoking directory is not it.

    This is the case the command exists for — proposal 010's executor runs from
    inside a worktree — and taking the invocation root for "main" would offer
    the real main worktree for removal.
    """

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-work")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "--quiet", str(linked), "feat/CR-001-work")
    monkeypatch.chdir(linked)

    assert main(["prune"]) == 0

    output = capsys.readouterr().out
    assert f"skipped: {repo} (branch master; main worktree)" in output
    assert f"eligible: {repo}" not in output


def test_a_worktree_hiding_untracked_files_is_not_called_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """status.showUntrackedFiles=no would otherwise make it read as clean.

    Untracked files in a worktree exist nowhere else, which is the whole reason
    a worktree carries a cleanliness condition its branch does not.
    """

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-work")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "--quiet", str(linked), "feat/CR-001-work")
    _git(repo, "config", "status.showUntrackedFiles", "no")
    (linked / "notes.txt").write_text("work that exists nowhere else", encoding="utf-8")

    assert main(["prune"]) == 0

    output = capsys.readouterr().out
    assert f"skipped: {linked}" in output
    assert "worktree is dirty" in output
    assert f"eligible: {linked}" not in output


def test_the_worktree_you_are_standing_in_is_never_offered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """git removes the current worktree without complaint; we must not ask it to.

    Doing so leaves the caller in a directory that no longer exists and the rest
    of the run failing on it — the same reason CR-059 never offers the branch
    that is checked out.
    """

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-work")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "--quiet", str(linked), "feat/CR-001-work")
    monkeypatch.chdir(linked)

    assert main(["prune"]) == 0

    output = capsys.readouterr().out
    assert (
        f"skipped: {linked} (branch feat/CR-001-work; the worktree you are in)"
        in output
    )
    assert f"eligible: {linked}" not in output


def test_a_subdirectory_of_the_current_worktree_is_still_the_current_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The project root is found by walking up, so depth does not change it.

    Pinned because it is not obvious from the comparison alone: the check reads
    as "path == project_root", and project_root is derived from the working
    directory rather than being it.
    """

    repo = _repo(tmp_path, monkeypatch)
    _git(repo, "branch", "feat/CR-001-work")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "--quiet", str(linked), "feat/CR-001-work")
    nested = linked / "deep" / "nested"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert main(["prune"]) == 0

    output = capsys.readouterr().out
    assert (
        f"skipped: {linked} (branch feat/CR-001-work; the worktree you are in)"
        in output
    )
    assert f"eligible: {linked}" not in output
