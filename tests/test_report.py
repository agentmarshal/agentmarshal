"""Tests for attributed session records and delegation reports."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import status
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_completed_record,
    create_session_record,
    read_records,
    write_record,
)
from agentmarshal.journal.report import build_report


def _initialize_repo(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo / ".agentmarshal" / "journal"


def _open_tasks() -> None:
    assert main(["open", "--title", "Completed task"]) == 0
    assert main(["open", "--title", "Abandoned task"]) == 0


def test_session_record_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "record-session",
                "--task",
                "CR-001",
                "--role",
                "implementer",
                "--actor",
                "vendor/model",
                "--activity",
                "implementation",
                "--outcome",
                "implemented",
                "--input-tokens",
                "12",
                "--output-tokens",
                "8",
                "--cache-tokens",
                "3",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.endswith("-session.json\n")
    record = read_records(journal, "CR-001")[-1]
    assert record["role"] == "implementer"
    assert record["tokens"] == {"input": 12, "output": 8, "cache": 3}


@pytest.mark.parametrize(
    ("role", "actor", "activity", "tokens", "error"),
    [
        ("r", "a", "invalid", (0, 0, 0), "activity"),
        ("r", "a", "other", (-1, 0, 0), "token 'input'"),
        ("", "a", "other", (0, 0, 0), "field 'role'"),
        ("r", "", "other", (0, 0, 0), "field 'actor'"),
    ],
)
def test_session_record_rejects_invalid_data_on_write(
    tmp_path: Path,
    role: str,
    actor: str,
    activity: str,
    tokens: tuple[int, int, int],
    error: str,
) -> None:
    record = create_session_record(
        "CR-001", "1.0", role, actor, activity, "outcome", *tokens
    )

    with pytest.raises(JournalRecordError, match=error):
        write_record(tmp_path / "journal", "CR-001", record)


def test_session_record_rejects_invalid_data_on_load(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    record = create_session_record(
        "CR-001", "1.0", "role", "actor", "other", "outcome", 0, 0, 0
    )
    record["tokens"] = {"input": 0, "output": -1, "cache": 0}
    records_directory = root / "tasks" / "CR-001" / "records"
    records_directory.mkdir(parents=True)
    (records_directory / "01J00000000000000000000000-session.json").write_text(
        json.dumps(record), encoding="utf-8"
    )

    with pytest.raises(JournalRecordError, match="token 'output'"):
        read_records(root, "CR-001")


def test_session_record_rejects_non_integer_token_on_write(tmp_path: Path) -> None:
    record = create_session_record(
        "CR-001", "1.0", "role", "actor", "other", "outcome", 0, 0, 0
    )
    record["tokens"] = {"input": True, "output": 0, "cache": 0}

    with pytest.raises(JournalRecordError, match="token 'input'"):
        write_record(tmp_path / "journal", "CR-001", record)


def test_report_includes_mixed_actor_sessions_and_terminal_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open_tasks()
    capsys.readouterr()
    for task_id, actor, token_count in (
        ("CR-001", "vendor/model", 9),
        ("CR-001", "human", 6),
        ("CR-002", "assistant", 15),
    ):
        assert (
            main(
                [
                    "record-session",
                    "--task",
                    task_id,
                    "--role",
                    "worker",
                    "--actor",
                    actor,
                    "--activity",
                    "other",
                    "--outcome",
                    "done",
                    "--input-tokens",
                    str(token_count),
                ]
            )
            == 0
        )
    for task_id in ("CR-001", "CR-001", "CR-002"):
        assert (
            main(
                [
                    "submit-review",
                    "--task",
                    task_id,
                    "--commit",
                    "a" * 40,
                    "--verdict",
                    "approved",
                    "--role",
                    "reviewer",
                    "--vendor",
                    "test",
                    "--model",
                    "model",
                    "--email",
                    "reviewer@test.invalid",
                ]
            )
            == 0
        )
    write_record(journal, "CR-001", create_completed_record("CR-001", "1.0", "a" * 40))
    write_record(journal, "CR-002", create_abandoned_record("CR-002", "1.0", "stop"))
    capsys.readouterr()

    assert main(["report"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "CR-001\tdone\treviews=2\ttokens=15",
        "CR-002\tabandoned\treviews=1\ttokens=15",
        "Summary\tabandoned=1 done=1\treviews=3\ttokens=30",
    ]


def test_report_for_one_task_and_empty_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    _initialize_repo(repo, monkeypatch)
    capsys.readouterr()

    assert main(["report"]) == 0
    assert capsys.readouterr().out == "Summary\t\treviews=0\ttokens=0\n"

    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    assert main(["report", "--task", "CR-001"]) == 0
    assert capsys.readouterr().out == "CR-001\topen\treviews=0\ttokens=0\n"


def test_task_scoped_report_ignores_unrelated_malformed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    assert main(["open", "--title", "Requested task"]) == 0
    assert main(["open", "--title", "Broken task"]) == 0

    # Corrupt an unrelated task's records: a task-scoped report must not
    # scan or validate it (ADR-0004).
    broken = journal / "tasks" / "CR-002" / "records"
    (next(broken.glob("*-opened.json"))).write_text("not json\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert capsys.readouterr().out == "CR-001\topen\treviews=0\ttokens=0\n"

    # The unfiltered report still surfaces the corruption fail-closed.
    assert main(["report"]) == 1


def test_report_uses_each_task_status_record_snapshot_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open_tasks()
    capsys.readouterr()
    calls: list[str] = []

    def track_read_records(journal_root: Path, task_id: str) -> list[dict[str, object]]:
        calls.append(task_id)
        return read_records(journal_root, task_id)

    monkeypatch.setattr(status, "read_records", track_read_records)

    build_report(journal)

    assert calls == ["CR-001", "CR-002"]
