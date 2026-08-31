"""Tests for operator acceptance over review findings."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_completed_record,
    read_records,
    write_record,
)
from agentmarshal.journal.status import project_status


def _run_git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _initialize_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "--quiet")
    _run_git(repo, "config", "user.name", "Operator")
    _run_git(repo, "config", "user.email", "operator@example.invalid")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Acceptance task"]) == 0
    _run_git(repo, "add", ".agentmarshal")
    _run_git(repo, "commit", "--quiet", "-m", "open task")
    commit = _run_git(repo, "rev-parse", "HEAD")
    return repo, repo / ".agentmarshal" / "journal", commit


def _review(commit: str, verdict: str, *findings: str) -> int:
    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--verdict",
        verdict,
        "--role",
        "reviewer",
        "--vendor",
        "test",
        "--model",
        "model",
        "--email",
        "reviewer@example.invalid",
    ]
    for finding in findings:
        arguments.extend(["--finding", finding])
    return main(arguments)


def _accept(commit: str, *extra: str) -> int:
    return main(
        [
            "accept",
            "--task",
            "CR-001",
            "--commit",
            commit,
            "--by",
            "operator@example.invalid",
            "--reason",
            "The review loop did not converge",
            *extra,
        ]
    )


def test_acceptance_derives_findings_validates_and_does_not_project_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, journal, commit = _initialize_task(tmp_path, monkeypatch)
    assert _review(commit, "changes_required", "F-2", "F-1") == 0
    capsys.readouterr()

    assert _accept(commit) == 0
    assert capsys.readouterr().out.endswith("-acceptance.json\n")
    records = read_records(journal, "CR-001")
    acceptance = records[-1]
    assert acceptance["record_type"] == "acceptance"
    assert acceptance["accepted_by"] == "operator@example.invalid"
    assert acceptance["accepted_commit"] == commit
    assert acceptance["findings"] == ["F-2", "F-1"]
    assert acceptance["reason"] == "The review loop did not converge"
    assert project_status(records) == "open"

    assert main(["validate"]) == 0
    assert "validate: passed" in capsys.readouterr().out


def test_acceptance_uses_latest_review_and_names_approving_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, journal, commit = _initialize_task(tmp_path, monkeypatch)
    assert _review(commit, "changes_required", "F-1") == 0
    assert _review(commit, "approved") == 0
    capsys.readouterr()

    assert _accept(commit) == 1
    error = capsys.readouterr().err
    assert "latest review verdict" in error
    assert "was approved" in error
    assert all(
        record["record_type"] != "acceptance"
        for record in read_records(journal, "CR-001")
    )


def test_acceptance_refuses_without_review_of_exact_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, _, commit = _initialize_task(tmp_path, monkeypatch)
    assert _review("b" * 40, "blocked", "F-1") == 0
    capsys.readouterr()

    assert _accept(commit) == 1
    error = capsys.readouterr().err
    assert "latest review verdict" in error
    assert "was none" in error
    assert "exact commit" in error


@pytest.mark.parametrize(
    ("arguments", "difference"),
    [
        (("--finding", "F-1"), "missing: F-2"),
        (
            ("--finding", "F-1", "--finding", "F-2", "--finding", "F-3"),
            "extra: F-3",
        ),
    ],
)
def test_acceptance_refuses_supplied_findings_that_differ(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: tuple[str, ...],
    difference: str,
) -> None:
    _, _, commit = _initialize_task(tmp_path, monkeypatch)
    assert _review(commit, "rejected", "F-1", "F-2") == 0
    capsys.readouterr()

    assert _accept(commit, *arguments) == 1
    assert difference in capsys.readouterr().err


def test_acceptance_refuses_task_with_terminal_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, journal, commit = _initialize_task(tmp_path, monkeypatch)
    assert _review(commit, "blocked", "F-1") == 0
    write_record(journal, "CR-001", create_completed_record("CR-001", "1.0", commit))
    capsys.readouterr()

    assert _accept(commit) == 1
    assert "terminal record" in capsys.readouterr().err


def test_status_summarizes_acceptance_trail_and_self_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, _, commit = _initialize_task(tmp_path, monkeypatch)
    assert _review(commit, "blocked", "F-1") == 0
    assert _accept(commit) == 0
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0
    output = capsys.readouterr().out
    assert "Status: open" in output
    assert "Acceptance: accepted over findings by operator@example.invalid" in output
    assert "self-accepted" in output
    assert "acceptance" in output
    assert f"accepted_commit={commit[:7]}" in output
    assert "findings=F-1" in output
