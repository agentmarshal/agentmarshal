"""Tests for completion and abandonment — closing the v2 loop."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import read_records
from agentmarshal.journal.status import (
    TaskStatusError,
    load_task_status,
    project_status,
)

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]
_REVIEWER_EMAIL = "reviewer@test.invalid"


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, check=True, capture_output=True, encoding="utf-8"
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Loop task", "--scope", "src/"]) == 0
    base = _commit_all(repo, "open task")
    return repo, base


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def test_full_loop_open_review_gate_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = _repo(tmp_path, monkeypatch)

    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement")

    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                _REVIEWER_EMAIL,
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "complete",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--pipeline-sha",
                head,
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "completed" in output

    records = read_records(_journal(repo), "CR-001")
    assert records[-1]["record_type"] == "completed"
    assert records[-1]["completed_commit"] == head
    assert load_task_status(_journal(repo), "CR-001").state == "done"


def test_complete_refused_when_gate_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = _repo(tmp_path, monkeypatch)
    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement without review")
    capsys.readouterr()

    # No review recorded: the gate refuses, so nothing is completed.
    assert (
        main(
            [
                "complete",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--pipeline-sha",
                head,
            ]
        )
        == 1
    )

    assert all(
        record["record_type"] != "completed"
        for record in read_records(_journal(repo), "CR-001")
    )
    assert load_task_status(_journal(repo), "CR-001").state == "open"


def test_abandon_open_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _base = _repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["abandon", "--task", "CR-001", "--reason", "superseded"]) == 0
    assert "abandoned" in capsys.readouterr().out

    records = read_records(_journal(repo), "CR-001")
    assert records[-1]["record_type"] == "abandoned"
    assert records[-1]["reason"] == "superseded"
    assert load_task_status(_journal(repo), "CR-001").state == "abandoned"


def test_abandon_refused_on_terminal_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _base = _repo(tmp_path, monkeypatch)
    assert main(["abandon", "--task", "CR-001", "--reason", "superseded"]) == 0
    capsys.readouterr()

    assert main(["abandon", "--task", "CR-001", "--reason", "again"]) == 1
    assert "not open" in capsys.readouterr().err
    assert (
        sum(
            record["record_type"] == "abandoned"
            for record in read_records(_journal(repo), "CR-001")
        )
        == 1
    )


def test_projection_rejects_record_after_terminal(tmp_path: Path) -> None:
    from agentmarshal.journal.records import (
        create_abandoned_record,
        create_completed_record,
        create_opened_record,
        create_review_record,
    )

    after_terminal = [
        create_opened_record("CR-001", "1.0"),
        create_completed_record("CR-001", "1.0", "a" * 40),
        create_review_record(
            "CR-001", "1.0", "a" * 40, "approved", "r", "v", "m", "r@t.i", []
        ),
    ]
    with pytest.raises(TaskStatusError, match="after a terminal record"):
        project_status(after_terminal)

    both_terminal = [
        create_opened_record("CR-001", "1.0"),
        create_completed_record("CR-001", "1.0", "a" * 40),
        create_abandoned_record("CR-001", "1.0", "reason"),
    ]
    with pytest.raises(TaskStatusError, match="after a terminal record"):
        project_status(both_terminal)


def test_projection_admits_session_after_terminal(tmp_path: Path) -> None:
    from agentmarshal.journal.records import (
        create_completed_record,
        create_opened_record,
        create_session_record,
    )

    # Measurements are not lifecycle (ADR-0005 Decision 3): a session
    # record accrues after a terminal record and leaves the state terminal.
    records = [
        create_opened_record("CR-001", "1.0"),
        create_completed_record("CR-001", "1.0", "a" * 40),
        create_session_record(
            "CR-001", "1.0", "lead", "opus", "implementation", "done", 1, 2, 3
        ),
    ]

    assert project_status(records) == "done"
