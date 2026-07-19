"""Tests for the read-only review launcher."""

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import review
from agentmarshal.journal.records import read_records


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _review_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--allow-empty",
        "--quiet",
        "-m",
        "init",
    )
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Review task"]) == 0
    return repo, _git(repo, "rev-parse", "HEAD")


def _reviewer_stub(tmp_path: Path, output: str, exit_code: int = 0) -> Path:
    stub = tmp_path / "reviewer.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stdout.write({output!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def _review_args(commit: str) -> list[str]:
    return [
        "review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--base",
        "HEAD",
        "--role",
        "reviewer",
        "--vendor",
        "test",
        "--model",
        "test-model",
    ]


def _verdict(commit: str, verdict: str, findings: list[str]) -> str:
    data = {"reviewed_commit": commit, "verdict": verdict, "findings": findings}
    return f"AGENTMARSHAL_VERDICT_BEGIN\n{json.dumps(data)}\nAGENTMARSHAL_VERDICT_END\n"


def _assert_no_snapshot(repo: Path) -> None:
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_failed_worktree_add_leaves_no_snapshot_or_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    original_run_git = review._run_git

    # Simulate git creating/registering the worktree and then exiting
    # non-zero: the real add runs, the wrapper still reports failure.
    def add_then_fail(project_root: Path, arguments: list[str]) -> str:
        result = original_run_git(project_root, arguments)
        if arguments[:2] == ["worktree", "add"]:
            raise review.ReviewLaunchError("worktree add exited non-zero")
        return result

    monkeypatch.setattr(review, "_run_git", add_then_fail)

    assert main(_review_args(commit)) == 1

    monkeypatch.setattr(review, "_run_git", original_run_git)
    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


def test_default_codex_adapter_uses_read_only_stdin_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)
    prompt_file = tmp_path / "review-prompt.txt"

    assert review._reviewer_command("codex", "test-model", prompt_file) == [
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--model",
        "test-model",
        "-",
    ]


def test_review_cleanup_failure_does_not_record_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    original_run_git = review._run_git

    def cleanup_then_fail(project_root: Path, arguments: list[str]) -> str:
        result = original_run_git(project_root, arguments)
        if arguments[:3] == ["worktree", "remove", "--force"]:
            raise review.ReviewLaunchError("worktree cleanup could not be confirmed")
        return result

    monkeypatch.setattr(review, "_run_git", cleanup_then_fail)

    assert main(_review_args(commit)) == 1

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


def test_review_recovers_from_failed_worktree_removal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    original_run_git = review._run_git

    def fail_worktree_removal(project_root: Path, arguments: list[str]) -> str:
        if arguments[:3] == ["worktree", "remove", "--force"]:
            raise review.ReviewLaunchError("simulated failure")
        return original_run_git(project_root, arguments)

    monkeypatch.setattr(review, "_run_git", fail_worktree_removal)

    assert main(_review_args(commit)) == 1

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


@pytest.mark.parametrize(
    ("verdict", "findings"),
    [("approved", []), ("changes_required", ["F-001"])],
)
def test_review_records_stub_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    verdict: str,
    findings: list[str],
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, verdict, findings))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(_review_args(commit)) == 0

    records = read_records(repo / ".agentmarshal" / "journal", "CR-001")
    assert records[-1]["reviewed_commit"] == commit
    assert records[-1]["verdict"] == verdict
    assert records[-1]["findings"] == findings
    capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    assert "reviewed_commit=" in main_output(capsys)
    _assert_no_snapshot(repo)


def main_output(capsys: pytest.CaptureFixture[str]) -> str:
    return capsys.readouterr().out


@pytest.mark.parametrize(
    "case",
    [
        "adapter_failure",
        "missing_sentinels",
        "invalid_json",
        "commit_mismatch",
        "rejected_verdict",
    ],
)
def test_review_failure_leaves_no_record_or_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    output = {
        "adapter_failure": "",
        "missing_sentinels": "not a verdict\n",
        "invalid_json": "AGENTMARSHAL_VERDICT_BEGIN\nnope\nAGENTMARSHAL_VERDICT_END\n",
        "commit_mismatch": _verdict("0" * 40, "approved", []),
        "rejected_verdict": _verdict(commit, "approved", ["F-001"]),
    }[case]
    exit_code = 1 if case == "adapter_failure" else 0
    stub = _reviewer_stub(tmp_path, output, exit_code)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(_review_args(commit)) == 1

    assert read_records(repo / ".agentmarshal" / "journal", "CR-001")
    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


@pytest.mark.parametrize(
    ("task", "commit"),
    [("CR-999", "HEAD"), ("CR-001", "not-a-commit")],
)
def test_review_rejects_unknown_task_or_commit_before_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    task: str,
    commit: str,
) -> None:
    repo, head = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(head, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    arguments = _review_args(commit)
    arguments[arguments.index("CR-001")] = task

    assert main(arguments) == 1

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)
