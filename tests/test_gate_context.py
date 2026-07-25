"""Tests for gate context derivation (CR-017)."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import GateError, run_gate
from agentmarshal.journal.gate_context import (
    GateContext,
    derive_gate_context,
    derive_task_from_branch,
    resolve_default_base,
)

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]
_REVIEWER_EMAIL = "reviewer@test.invalid"


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _opened_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """Initialized repo with an opened task committed on master."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Gate task", "--scope", "src/"]) == 0
    base = _commit_all(repo, "open task")
    return repo, base


def _approve(repo: Path, commit: str, email: str = _REVIEWER_EMAIL) -> None:
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                email,
            ]
        )
        == 0
    )


# --- pure branch -> task derivation ---------------------------------------


def test_derive_task_from_branch_extracts_id() -> None:
    assert derive_task_from_branch("feat/CR-001-slug") == "CR-001"
    assert derive_task_from_branch("completion/CR-042-thing") == "CR-042"


def test_derive_task_from_branch_fails_closed_without_id() -> None:
    with pytest.raises(GateError, match="does not encode a task id"):
        derive_task_from_branch("wip/no-task-here")


# --- context derivation from the git checkout ------------------------------


def test_derive_gate_context_from_branch_and_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _base = _opened_repo(tmp_path, monkeypatch)
    _git(repo, "switch", "--quiet", "-c", "feat/CR-001-work")
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement")

    context = derive_gate_context(repo, None, None, None)

    assert context == GateContext(task="CR-001", commit=head, base="master")


def test_derive_gate_context_explicit_overrides_without_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _base = _opened_repo(tmp_path, monkeypatch)
    head = _git(repo, "rev-parse", "HEAD")
    # Detach HEAD: fully explicit inputs must not require a branch at all.
    _git(repo, "checkout", "--quiet", head)

    context = derive_gate_context(repo, "CR-009", head, "develop")

    assert context == GateContext(task="CR-009", commit=head, base="develop")


def test_derive_task_fails_closed_on_detached_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _opened_repo(tmp_path, monkeypatch)
    _git(repo, "checkout", "--quiet", base)  # detached HEAD

    with pytest.raises(GateError, match="detached"):
        derive_gate_context(repo, None, base, "master")


def test_derive_commit_fails_closed_on_unborn_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "feat/CR-001-x")

    with pytest.raises(GateError):
        derive_gate_context(repo, "CR-001", None, "master")


def test_resolve_default_base_falls_back_to_local_master(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _base = _opened_repo(tmp_path, monkeypatch)
    # No origin remote here, but a local master exists.
    assert resolve_default_base(repo) == "master"


def test_resolve_default_base_fails_closed_without_master(tmp_path: Path) -> None:
    repo = tmp_path / "other"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "trunk")
    _git(repo, *_WRITER, "commit", "--quiet", "--allow-empty", "-m", "root")

    with pytest.raises(GateError, match="default base branch"):
        resolve_default_base(repo)


# --- end-to-end: derived invocation equals the explicit one ----------------


def test_cli_gate_derives_context_matching_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _base = _opened_repo(tmp_path, monkeypatch)
    _git(repo, "switch", "--quiet", "-c", "feat/CR-001-work")
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement")
    _approve(repo, head)

    explicit = run_gate(repo, "CR-001", head, "master", head)
    assert explicit.passed

    # No --task/--commit/--base: everything derived from the checkout.
    exit_code = main(["gate", "--pipeline-sha", head])
    captured = capsys.readouterr()

    assert exit_code == 0, captured.err
    assert "gate: passed" in captured.out
    assert captured.out.count("FAIL") == 0
