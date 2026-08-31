"""Tests for reopening completed tasks without rewriting their history."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_abandoned_record,
    create_completed_record,
    create_opened_record,
    create_reopened_record,
    create_review_record,
    read_records,
    write_record,
)
from agentmarshal.journal.status import (
    TaskStatusError,
    load_task_status,
    project_status,
)


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Reopen task", "--scope", "src/"]) == 0
    return repo, repo / ".agentmarshal" / "journal"


def _complete(journal: Path) -> None:
    write_record(
        journal,
        "CR-001",
        create_completed_record("CR-001", "test", "a" * 40),
    )


def test_reopen_records_reason_projects_open_and_validates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _repo_path, journal = _repo(tmp_path, monkeypatch)
    _complete(journal)
    capsys.readouterr()

    reason = "The implementation missed an edge case"
    assert main(["reopen", "--task", "CR-001", "--reason", reason]) == 0
    assert "reopened" in capsys.readouterr().out

    records = read_records(journal, "CR-001")
    reopening = records[-1]
    assert reopening["record_type"] == "reopened"
    assert reopening["reason"] == reason
    assert load_task_status(journal, "CR-001").state == "open"

    assert main(["status", "CR-001"]) == 0
    output = capsys.readouterr().out
    assert "Status: open" in output
    assert f"reopened {reopening['created_at']} reason={reason}" in output

    assert main(["validate"]) == 0
    assert "validate: passed" in capsys.readouterr().out


def test_reopen_refuses_open_unknown_and_abandoned_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _repo_path, journal = _repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["reopen", "--task", "CR-001", "--reason", "More work"]) == 1
    assert "task CR-001 cannot be reopened (state: open)" in capsys.readouterr().err

    assert main(["reopen", "--task", "CR-999", "--reason", "Found it"]) == 1
    assert "unknown task id: CR-999" in capsys.readouterr().err

    write_record(
        journal,
        "CR-001",
        create_abandoned_record("CR-001", "test", "Wrong work"),
    )
    assert main(["reopen", "--task", "CR-001", "--reason", "Try again"]) == 1
    assert (
        "task CR-001 cannot be reopened (state: abandoned)" in capsys.readouterr().err
    )


@pytest.mark.parametrize("reason", ["", "   "])
def test_reopen_refuses_empty_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reason: str,
) -> None:
    _repo_path, journal = _repo(tmp_path, monkeypatch)
    _complete(journal)
    capsys.readouterr()

    assert main(["reopen", "--task", "CR-001", "--reason", reason]) == 1
    assert "reopen reason must not be empty" in capsys.readouterr().err
    assert [record["record_type"] for record in read_records(journal, "CR-001")] == [
        "opened",
        "completed",
    ]


def test_projection_allows_work_and_another_terminal_after_reopening() -> None:
    records = [
        create_opened_record("CR-001", "test"),
        create_completed_record("CR-001", "test", "a" * 40),
        create_reopened_record("CR-001", "test", "Review missed a case"),
        create_review_record(
            "CR-001",
            "test",
            "b" * 40,
            "approved",
            "reviewer",
            "vendor",
            "model",
            "reviewer@example.test",
            [],
        ),
        create_completed_record("CR-001", "test", "b" * 40),
    ]

    assert project_status(records[:-1]) == "open"
    assert project_status(records) == "done"
    assert [record["record_type"] for record in records] == [
        "opened",
        "completed",
        "reopened",
        "review",
        "completed",
    ]


def test_projection_keeps_other_lifecycle_records_forbidden_after_terminal() -> None:
    records = [
        create_opened_record("CR-001", "test"),
        create_completed_record("CR-001", "test", "a" * 40),
        create_review_record(
            "CR-001",
            "test",
            "a" * 40,
            "approved",
            "reviewer",
            "vendor",
            "model",
            "reviewer@example.test",
            [],
        ),
    ]

    with pytest.raises(TaskStatusError, match="after a terminal record"):
        project_status(records)


def test_projection_rejects_reopening_without_completion() -> None:
    records = [
        create_opened_record("CR-001", "test"),
        create_reopened_record("CR-001", "test", "No close to reopen"),
    ]

    with pytest.raises(TaskStatusError, match="while it is open"):
        project_status(records)
