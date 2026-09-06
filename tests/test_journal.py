"""Tests for journal contracts, records, and task opening."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import (
    JournalContractError,
    JournalRecordError,
    create_opened_record,
    create_review_record,
    create_session_record,
    generate_ulid,
    parse_contract,
    project_status,
    read_records,
    write_record,
)
from agentmarshal.journal.open_task import TaskOpenError, journal_root, open_task
from agentmarshal.journal.records import (
    create_abandoned_record,
    create_completed_record,
)


def initialize_status_repo(repo: Path) -> Path:
    init_git_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    return journal_root(repo)


def init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )


def _commit_file(repo: Path, name: str, content: str) -> str:
    (repo / name).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            name,
        ],
        cwd=repo,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _without_recorder(record: dict[str, object]) -> dict[str, object]:
    """Drop the stamped actor pair, so a round-trip compares content only.

    write_record stamps recorded_by/recorded_by_source from the invoking
    identity (ADR-0006), which varies by machine. These assertions are about the
    record surviving the round trip unchanged, not about who wrote it.
    """

    return {
        key: value
        for key, value in record.items()
        if key not in {"recorded_by", "recorded_by_source"}
    }


def test_write_record_rejects_symlinked_journal_ancestor(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".agentmarshal").symlink_to(outside, target_is_directory=True)
    journal = repo / ".agentmarshal" / "journal"

    with pytest.raises(JournalRecordError):
        write_record(journal, "CR-001", create_opened_record("CR-001", "0.1.0.dev0"))

    assert list(outside.iterdir()) == []


def test_read_records_rejects_symlinked_journal_ancestor(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    (outside / "journal" / "tasks" / "CR-001" / "records").mkdir(parents=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".agentmarshal").symlink_to(outside, target_is_directory=True)
    journal = repo / ".agentmarshal" / "journal"

    with pytest.raises(JournalRecordError):
        read_records(journal, "CR-001")


@pytest.mark.parametrize("name", ["unexpected.txt", "invalid.json"])
def test_read_records_rejects_non_record_files(tmp_path: Path, name: str) -> None:
    records_directory = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_directory.mkdir(parents=True)
    invalid_record = records_directory / name
    invalid_record.write_text("not a record\n", encoding="utf-8")

    with pytest.raises(JournalRecordError, match=str(invalid_record)):
        read_records(tmp_path / "journal", "CR-001")


def test_read_records_rejects_nested_directory(tmp_path: Path) -> None:
    records_directory = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    nested_directory = records_directory / "nested"
    nested_directory.mkdir(parents=True)

    with pytest.raises(JournalRecordError, match=str(nested_directory)):
        read_records(tmp_path / "journal", "CR-001")


def test_generate_ulids_are_unique_and_lexicographically_ordered() -> None:
    identifiers = [generate_ulid() for _ in range(100)]

    assert len(set(identifiers)) == len(identifiers)
    assert identifiers == sorted(identifiers)
    assert all(len(identifier) == 26 for identifier in identifiers)


@pytest.mark.parametrize(
    ("content", "error"),
    [
        (
            "+++\nschema = 2\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
            "acceptance = []\n+++\n",
            "schema",
        ),
        (
            "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n+++\n",
            "acceptance",
        ),
    ],
)
def test_parse_contract_rejects_invalid_headers(
    tmp_path: Path, content: str, error: str
) -> None:
    contract = tmp_path / "contract.md"
    contract.write_text(content, encoding="utf-8")

    with pytest.raises(JournalContractError, match=error):
        parse_contract(contract)


def test_parse_contract_accepts_bom_prefixed_header(tmp_path: Path) -> None:
    contract = tmp_path / "contract.md"
    contract.write_text(
        "\ufeff+++\nschema = 1\nid = 'CR-001'\ntitle = 'Задача'\nscope = ['src/']\n"
        "acceptance = ['works']\n+++\n",
        encoding="utf-8",
    )

    assert parse_contract(contract).title == "Задача"


def test_write_record_is_exclusive_and_preserves_original_content(
    tmp_path: Path,
) -> None:
    root = tmp_path / "journal"
    record = create_opened_record("CR-001", "1.0")
    identifier = "01J00000000000000000000000"
    path = write_record(root, "CR-001", record, record_id=identifier)
    original = path.read_bytes()

    with pytest.raises(FileExistsError):
        write_record(root, "CR-001", record, record_id=identifier)

    assert path.read_bytes() == original
    assert [_without_recorder(r) for r in read_records(root, "CR-001")] == [
        record | {"id": identifier}
    ]


def test_builders_emit_schema_3_with_live_provenance(tmp_path: Path) -> None:
    # Forward capture is in-toto-complete from the start: builders emit
    # schema 3 with live provenance, and the record round-trips through the
    # validating writer/reader.
    record = create_opened_record("CR-001", "1.0")
    assert record["schema"] == 3
    assert record["source"] == "live"

    review = create_review_record(
        "CR-001", "1.0", "a" * 40, "approved", "r", "v", "m", "r@t.i", []
    )
    assert review["schema"] == 3
    assert review["source"] == "live"

    root = tmp_path / "journal"
    identifier = "01J00000000000000000000000"
    write_record(root, "CR-001", record, record_id=identifier)
    assert [_without_recorder(r) for r in read_records(root, "CR-001")] == [
        record | {"id": identifier}
    ]


@pytest.mark.parametrize("schema", [1, 2])
def test_existing_record_schemas_remain_valid(tmp_path: Path, schema: int) -> None:
    record = create_opened_record("CR-001", "1.0")
    record["schema"] = schema
    if schema == 1:
        record.pop("source")

    root = tmp_path / "journal"
    write_record(root, "CR-001", record, record_id="01J00000000000000000000000")

    assert read_records(root, "CR-001")[0]["schema"] == schema


def test_session_usage_round_trips_and_remains_optional(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    legacy = create_session_record(
        "CR-001", "0.1.0", "worker", "agent", "other", "done", 3, 2, 1
    )
    legacy["schema"] = 1
    legacy.pop("source")
    attributed = create_session_record(
        "CR-001",
        "1.0",
        "worker",
        "agent",
        "implementation",
        "done",
        6,
        4,
        2,
        usage_provider="example-provider",
        usage_method="reported",
    )

    write_record(root, "CR-001", legacy, record_id="01J00000000000000000000000")
    write_record(root, "CR-001", attributed, record_id="01J00000000000000000000001")

    records = [_without_recorder(record) for record in read_records(root, "CR-001")]
    assert "usage" not in records[0]
    assert records[1]["usage"] == {
        "provider": "example-provider",
        "method": "reported",
    }


@pytest.mark.parametrize(
    ("usage", "error"),
    [
        ({"provider": "example", "method": "estimated"}, "method"),
        ({"provider": "", "method": "measured"}, "provider"),
        ({"provider": "example", "method": "reported", "region": "us"}, "region"),
        ({"provider": "example"}, "usage"),
        ("reported by example", "object"),
    ],
)
def test_session_usage_rejects_malformed_values(
    tmp_path: Path, usage: object, error: str
) -> None:
    record = create_session_record(
        "CR-001", "1.0", "worker", "agent", "other", "done", 0, 0, 0
    )
    record["usage"] = usage

    with pytest.raises(JournalRecordError, match=error):
        write_record(tmp_path / "journal", "CR-001", record)


@pytest.mark.parametrize(
    ("argument", "missing"),
    [
        (("--usage-provider", "example"), "--usage-method"),
        (("--usage-method", "measured"), "--usage-provider"),
    ],
)
def test_record_session_requires_both_usage_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argument: tuple[str, str],
    missing: str,
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    arguments = [
        "record-session",
        "--task",
        "CR-001",
        "--role",
        "worker",
        "--actor",
        "agent",
        "--activity",
        "other",
        "--outcome",
        "done",
        *argument,
    ]
    assert main(arguments) == 1
    assert missing in capsys.readouterr().err
    assert [record["record_type"] for record in read_records(root, "CR-001")] == [
        "opened"
    ]


def test_record_session_writes_usage_and_validate_accepts_mixed_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    common = [
        "record-session",
        "--task",
        "CR-001",
        "--role",
        "worker",
        "--actor",
        "agent",
        "--activity",
        "other",
        "--outcome",
        "done",
    ]

    assert main(common) == 0
    assert (
        main(
            [
                *common,
                "--usage-provider",
                "example-provider",
                "--usage-method",
                "measured",
            ]
        )
        == 0
    )
    capsys.readouterr()

    sessions = [
        record
        for record in read_records(root, "CR-001")
        if record["record_type"] == "session"
    ]
    assert "usage" not in sessions[0]
    assert sessions[1]["usage"] == {
        "provider": "example-provider",
        "method": "measured",
    }
    assert main(["validate"]) == 0
    assert "validate: passed" in capsys.readouterr().out


def test_review_record_round_trip_and_status_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                "a" * 40,
                "--verdict",
                "changes_required",
                "--finding",
                "F-001",
                "--role",
                "reviewer",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                "reviewer@test.invalid",
            ]
        )
        == 0
    )
    records = read_records(root, "CR-001")
    assert records[-1]["reviewed_commit"] == "a" * 40
    assert records[-1]["findings"] == ["F-001"]

    capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    output = capsys.readouterr().out
    assert "reviewed_commit=aaaaaaa" in output
    assert "verdict=changes_required findings=1" in output


@pytest.mark.parametrize(
    ("reviewed_commit", "verdict", "findings", "reviewer", "error"),
    [
        ("a" * 40, "approved", ["F-001"], ("r", "v", "m", "r@t.i"), "approved"),
        (
            "a" * 40,
            "changes_required",
            [],
            ("r", "v", "m", "r@t.i"),
            "non-approved",
        ),
        ("a" * 39, "approved", [], ("r", "v", "m", "r@t.i"), "reviewed_commit"),
        ("g" * 40, "approved", [], ("r", "v", "m", "r@t.i"), "reviewed_commit"),
        (
            "a" * 40,
            "changes_required",
            ["F-001", "F-001"],
            ("r", "v", "m", "r@t.i"),
            "unique",
        ),
        ("a" * 40, "approved", [], ("", "v", "m", "r@t.i"), "reviewer field 'role'"),
        ("a" * 40, "approved", [], ("r", "v", "m", ""), "reviewer field 'email'"),
        ("a" * 40, "approved", [], ("r", "v", "m", "no-at"), "must contain '@'"),
    ],
)
def test_review_record_rejects_inconsistent_data_on_write(
    tmp_path: Path,
    reviewed_commit: str,
    verdict: str,
    findings: list[str],
    reviewer: tuple[str, str, str, str],
    error: str,
) -> None:
    record = create_review_record(
        "CR-001", "1.0", reviewed_commit, verdict, *reviewer, findings
    )

    with pytest.raises(JournalRecordError, match=error):
        write_record(tmp_path / "journal", "CR-001", record)


def test_read_records_rejects_inconsistent_review(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    record = create_review_record(
        "CR-001", "1.0", "a" * 40, "approved", "r", "v", "m", "r@t.i", ["F-001"]
    )
    records_directory = root / "tasks" / "CR-001" / "records"
    records_directory.mkdir(parents=True)
    (records_directory / "01J00000000000000000000000-review.json").write_text(
        json.dumps(record), encoding="utf-8"
    )

    with pytest.raises(JournalRecordError, match="approved"):
        read_records(root, "CR-001")


def test_submit_review_rejects_unknown_and_unopened_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        "a" * 40,
        "--verdict",
        "approved",
        "--role",
        "r",
        "--vendor",
        "v",
        "--model",
        "m",
        "--email",
        "r@t.i",
    ]
    assert main(arguments) == 1
    assert "unknown task id" in capsys.readouterr().err

    task_directory = root / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    assert main(arguments) == 1
    assert "do not contain an opened record" in capsys.readouterr().err
    assert not (task_directory / "records").exists()


def test_review_records_do_not_change_projected_status() -> None:
    records = [
        create_opened_record("CR-001", "1.0"),
        create_review_record(
            "CR-001", "1.0", "a" * 40, "approved", "r", "v", "m", "r@t.i", []
        ),
    ]

    assert project_status(records) == "open"


def test_amend_records_reason_without_changing_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    reason = "Clarify the review boundary"
    assert main(["amend", "--task", "CR-001", "--reason", reason]) == 0
    output = capsys.readouterr().out
    records = read_records(root, "CR-001")
    amendment = records[-1]
    assert output.strip().endswith(f"/{amendment['id']}-amendment.json")
    assert amendment["record_type"] == "amendment"
    assert amendment["reason"] == reason
    assert project_status(records) == "open"

    assert main(["status", "CR-001"]) == 0
    status_output = capsys.readouterr().out
    assert "Status: open" in status_output
    assert f"amendment {amendment['created_at']} reason={reason}" in status_output

    assert main(["validate"]) == 0
    assert "validate: passed" in capsys.readouterr().out


@pytest.mark.parametrize("reason", ["", "   "])
def test_amend_refuses_empty_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reason: str,
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    assert main(["amend", "--task", "CR-001", "--reason", reason]) == 1
    assert "reason must not be empty" in capsys.readouterr().err
    assert [record["record_type"] for record in read_records(root, "CR-001")] == [
        "opened"
    ]


def test_amend_requires_reason() -> None:
    with pytest.raises(SystemExit):
        main(["amend", "--task", "CR-001"])


def test_amend_refuses_unknown_and_terminal_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["amend", "--task", "CR-999", "--reason", "Correction"]) == 1
    assert "unknown task id: CR-999" in capsys.readouterr().err

    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    write_record(
        root,
        "CR-001",
        create_abandoned_record("CR-001", "1.0", "No longer needed"),
    )
    assert main(["amend", "--task", "CR-001", "--reason", "Too late"]) == 1
    assert "task CR-001 is not open (state: abandoned)" in capsys.readouterr().err
    assert [record["record_type"] for record in read_records(root, "CR-001")] == [
        "opened",
        "abandoned",
    ]


@pytest.mark.parametrize(
    "record",
    [
        {
            "schema": 1,
            "record_type": "unknown",
            "task": "CR-001",
            "created_at": "2026-07-19T00:00:00Z",
        },
        {
            "schema": 1,
            "record_type": "opened",
            "task": "CR-001",
            "created_at": "2026-07-19T00:00:00Z",
        },
    ],
)
def test_write_record_rejects_unsupported_or_incomplete_types(
    tmp_path: Path, record: dict[str, object]
) -> None:
    with pytest.raises(JournalRecordError):
        write_record(tmp_path / "journal", "CR-001", record)


@pytest.mark.parametrize(
    ("filename", "record"),
    [
        ("invalid.json", create_opened_record("CR-001", "1.0")),
        (
            "01J00000000000000000000000-closed.json",
            create_opened_record("CR-001", "1.0"),
        ),
    ],
)
def test_read_records_rejects_invalid_filename_or_type(
    tmp_path: Path, filename: str, record: dict[str, object]
) -> None:
    records_directory = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_directory.mkdir(parents=True)
    (records_directory / filename).write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(JournalRecordError):
        read_records(tmp_path / "journal", "CR-001")


@pytest.mark.parametrize("task_id", [".", "..", "CR-001/records"])
def test_records_reject_invalid_task_ids(tmp_path: Path, task_id: str) -> None:
    root = tmp_path / "journal"
    record = create_opened_record(task_id, "1.0")

    with pytest.raises(ValueError, match="task id"):
        write_record(root, task_id, record)
    with pytest.raises(ValueError, match="task id"):
        read_records(root, task_id)


def test_open_removes_staged_task_when_record_creation_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    (repo / ".agentmarshal").mkdir(parents=True)

    def fail_write(*_args: object, **_kwargs: object) -> Path:
        raise OSError("disk full")

    monkeypatch.setattr("agentmarshal.journal.open_task.write_record", fail_write)

    with pytest.raises(TaskOpenError, match="disk full"):
        open_task(repo, "Task", [])

    assert not (journal_root(repo) / "tasks" / "CR-001").exists()


def test_records_refuse_a_symlinked_task_directory(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    external = tmp_path / "external"
    external.mkdir()
    (root / "tasks").mkdir(parents=True)
    (root / "tasks" / "CR-001").symlink_to(external, target_is_directory=True)
    record = create_opened_record("CR-001", "1.0")

    with pytest.raises(JournalRecordError, match="symlink"):
        write_record(root, "CR-001", record)
    with pytest.raises(JournalRecordError, match="symlink"):
        read_records(root, "CR-001")

    assert not (external / "records").exists()


@pytest.mark.parametrize("component", ["metadata", "journal", "tasks"])
def test_open_refuses_symlinked_journal_components(
    tmp_path: Path, component: str
) -> None:
    repo = tmp_path / "repo"
    external = tmp_path / "external"
    external.mkdir()
    metadata = repo / ".agentmarshal"
    metadata.mkdir(parents=True)
    if component == "metadata":
        metadata.rmdir()
        metadata.symlink_to(external, target_is_directory=True)
    elif component == "journal":
        (metadata / "journal").symlink_to(external, target_is_directory=True)
    else:
        root = journal_root(repo)
        root.mkdir()
        (root / "tasks").symlink_to(external, target_is_directory=True)

    with pytest.raises(TaskOpenError, match="symlink"):
        open_task(repo, "Task", [])

    assert not (external / "tasks").exists()


def test_open_creates_parseable_contract_and_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)

    assert main(["open", "--title", "Задача", "--scope", "src/"]) == 0

    root = journal_root(repo)
    contract = parse_contract(root / "tasks" / "CR-001" / "contract.md")
    assert contract.title == "Задача"
    assert contract.scope == ("src/",)
    assert read_records(root, "CR-001")[0]["record_type"] == "opened"
    assert "contract.md" in capsys.readouterr().out


def test_open_fails_outside_an_initialized_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agentmarshal.cli.find_project_root", lambda _start: None)

    assert main(["open", "--title", "Task"]) == 1

    assert "initialized project" in capsys.readouterr().err
    assert not (tmp_path / ".agentmarshal").exists()


def test_open_allocates_an_id_after_existing_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    (journal_root(repo) / "tasks" / "CR-007").mkdir(parents=True)
    monkeypatch.chdir(repo)

    assert main(["open", "--title", "Task"]) == 0

    assert (journal_root(repo) / "tasks" / "CR-008" / "contract.md").is_file()


def test_open_allocates_an_id_after_legacy_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    legacy_task = journal_root(repo) / "tasks" / "done" / "2026" / "CR-007-task.md"
    legacy_task.parent.mkdir(parents=True)
    legacy_task.write_text("# CR-007\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert main(["open", "--title", "Task"]) == 0

    assert (journal_root(repo) / "tasks" / "CR-008" / "contract.md").is_file()


def test_status_lists_opened_tasks_with_cyrillic_titles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    initialize_status_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["open", "--title", "Задача", "--scope", "src/"]) == 0
    capsys.readouterr()
    assert main(["status"]) == 0

    output = capsys.readouterr().out
    assert "CR-001\topen\t" in output
    assert output.endswith("Задача\n")


def test_status_shows_task_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    initialize_status_repo(repo)
    monkeypatch.chdir(repo)

    assert (
        main(["open", "--title", "Task", "--scope", "src/", "--scope", "tests/"]) == 0
    )
    capsys.readouterr()
    assert main(["status", "CR-001"]) == 0

    output = capsys.readouterr().out
    record = read_records(journal_root(repo), "CR-001")[0]
    assert "ID: CR-001" in output
    assert "Status: open" in output
    assert "Title: Task" in output
    assert "- src/" in output
    assert "- tests/" in output
    assert str(record["id"]) in output
    assert str(record["record_type"]) in output
    assert str(record["created_at"]) in output


def test_status_reports_empty_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    initialize_status_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["status"]) == 0

    assert "no tasks" in capsys.readouterr().out.lower()


def test_status_rejects_unknown_task_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    initialize_status_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["status", "CR-999"]) == 1

    assert "unknown task id: CR-999" in capsys.readouterr().err


def test_status_rejects_task_without_opened_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    task_directory = root / "tasks" / "CR-001"
    (task_directory / "records").mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    assert main(["status", "CR-001"]) == 1

    assert "do not contain an opened record" in capsys.readouterr().err


def test_project_status_rejects_duplicate_opened_records() -> None:
    records = [
        create_opened_record("CR-001", "1.0"),
        create_opened_record("CR-001", "1.0"),
    ]

    with pytest.raises(ValueError, match="multiple opened records"):
        project_status(records)


def test_status_rejects_duplicate_opened_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    task_directory = root / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    write_record(root, "CR-001", create_opened_record("CR-001", "1.0"))
    write_record(root, "CR-001", create_opened_record("CR-001", "1.0"))
    monkeypatch.chdir(repo)

    assert main(["status", "CR-001"]) == 1

    assert "multiple opened records" in capsys.readouterr().err


def test_status_lists_task_ids_in_numeric_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    for task_id in ("CR-999", "CR-1000"):
        task_directory = root / "tasks" / task_id
        task_directory.mkdir(parents=True)
        (task_directory / "contract.md").write_text(
            f"+++\nschema = 1\nid = '{task_id}'\ntitle = 'Task'\nscope = []\n"
            "acceptance = []\n+++\n",
            encoding="utf-8",
        )
        write_record(root, task_id, create_opened_record(task_id, "1.0"))
    monkeypatch.chdir(repo)

    assert main(["status"]) == 0

    output = capsys.readouterr().out
    assert output.index("CR-999") < output.index("CR-1000")


def test_status_reports_malformed_record_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    task_directory = root / "tasks" / "CR-001"
    records_directory = task_directory / "records"
    records_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    malformed = records_directory / "01J00000000000000000000000-opened.json"
    malformed.write_text("{", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert main(["status"]) == 1

    assert str(malformed) in capsys.readouterr().err


def test_status_rejects_symlinked_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    task_directory = root / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    external_contract = tmp_path / "contract.md"
    external_contract.write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    (task_directory / "contract.md").symlink_to(external_contract)
    write_record(root, "CR-001", create_opened_record("CR-001", "1.0"))
    monkeypatch.chdir(repo)

    assert main(["status"]) == 1

    assert str(task_directory / "contract.md") in capsys.readouterr().err


def test_status_rejects_symlinked_journal_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    external = tmp_path / "external"
    (external / "journal" / "tasks" / "CR-001").mkdir(parents=True)
    (external / "project.json").write_text('{"schema": 1}\n', encoding="utf-8")
    (external / "journal" / "tasks" / "CR-001" / "contract.md").write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    (repo / ".agentmarshal").symlink_to(external, target_is_directory=True)
    monkeypatch.chdir(repo)

    assert main(["status"]) == 1

    assert "symlink" in capsys.readouterr().err


def test_status_accepts_bom_prefixed_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    task_directory = root / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "\ufeff+++\nschema = 1\nid = 'CR-001'\ntitle = 'Задача'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    write_record(root, "CR-001", create_opened_record("CR-001", "1.0"))
    monkeypatch.chdir(repo)

    assert main(["status"]) == 0

    assert "Задача" in capsys.readouterr().out


def _review_with_advisory(advisory: list[str]) -> dict[str, object]:
    return create_review_record(
        "CR-001",
        "1.0",
        "a" * 40,
        "approved",
        "r",
        "v",
        "m",
        "r@t.i",
        [],
        advisory_findings=advisory,
    )


def test_approved_review_with_advisory_findings_round_trips(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    record = _review_with_advisory(["F1", "F2"])
    assert record["verdict"] == "approved"
    assert record["findings"] == []
    assert record["advisory_findings"] == ["F1", "F2"]
    identifier = "01J00000000000000000000000"
    write_record(root, "CR-001", record, record_id=identifier)
    assert [_without_recorder(r) for r in read_records(root, "CR-001")] == [
        record | {"id": identifier}
    ]


def test_review_without_advisory_omits_the_field() -> None:
    record = create_review_record(
        "CR-001", "1.0", "a" * 40, "approved", "r", "v", "m", "r@t.i", []
    )
    assert "advisory_findings" not in record


def test_advisory_findings_must_be_unique_non_empty_and_disjoint(
    tmp_path: Path,
) -> None:
    for advisory in (["", "F1"], ["F1", "F1"]):
        with pytest.raises(JournalRecordError, match="advisory_findings"):
            write_record(tmp_path / "j", "CR-001", _review_with_advisory(advisory))
    # A finding cannot be both blocking and advisory.
    record = create_review_record(
        "CR-001",
        "1.0",
        "a" * 40,
        "changes_required",
        "r",
        "v",
        "m",
        "r@t.i",
        ["F1"],
        advisory_findings=["F1"],
    )
    with pytest.raises(JournalRecordError, match="disjoint"):
        write_record(tmp_path / "j2", "CR-001", record)


def test_approved_review_still_rejects_blocking_findings(tmp_path: Path) -> None:
    record = create_review_record(
        "CR-001",
        "1.0",
        "a" * 40,
        "approved",
        "r",
        "v",
        "m",
        "r@t.i",
        ["F1"],
        advisory_findings=["F2"],
    )
    with pytest.raises(JournalRecordError, match="approved review records"):
        write_record(tmp_path / "j", "CR-001", record)


def test_scope_warning_names_a_directory_missing_its_slash(tmp_path: Path) -> None:
    """The reported failure: `--scope src` gates everything under src/ as outside."""

    from agentmarshal.journal.open_task import scope_warnings

    (tmp_path / "src").mkdir()

    warnings = scope_warnings(tmp_path, ["src"])

    assert len(warnings) == 1
    assert "src" in warnings[0]
    assert "'src/'" in warnings[0]


def test_scope_warning_for_a_path_that_is_not_there(tmp_path: Path) -> None:
    from agentmarshal.journal.open_task import scope_warnings

    warnings = scope_warnings(tmp_path, ["nowhere/", "missing.py"])

    assert len(warnings) == 2
    assert all("matches no path" in warning for warning in warnings)


def test_scope_warning_stays_silent_when_entries_match(tmp_path: Path) -> None:
    from agentmarshal.journal.open_task import scope_warnings

    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("x", encoding="utf-8")

    assert scope_warnings(tmp_path, ["src/", "README.md"]) == []


def test_scope_warning_for_no_declared_scope(tmp_path: Path) -> None:
    from agentmarshal.journal.open_task import scope_warnings

    warnings = scope_warnings(tmp_path, [])

    assert len(warnings) == 1
    assert "declares no scope" in warnings[0]
    assert "no change can land until one is declared" in warnings[0]


def test_open_warns_but_still_opens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A warning must never become a refusal: a task may declare what it creates."""

    import subprocess

    from agentmarshal.cli import main

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    capsys.readouterr()

    assert main(["open", "--title", "T", "--scope", "not-created-yet/"]) == 0

    captured = capsys.readouterr()
    assert "matches no path" in captured.err
    assert "contract.md" in captured.out
    assert (repo / ".agentmarshal/journal/tasks/CR-001/contract.md").is_file()


def test_open_without_scope_warns_but_still_opens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    capsys.readouterr()

    assert main(["open", "--title", "T"]) == 0

    captured = capsys.readouterr()
    assert "declares no scope" in captured.err
    assert "no change can land until one is declared" in captured.err
    assert "declares no scope" not in captured.out
    assert "contract.md" in captured.out
    assert (repo / ".agentmarshal/journal/tasks/CR-001/contract.md").is_file()


def test_open_with_scope_does_not_warn_that_scope_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tracked.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    capsys.readouterr()

    assert main(["open", "--title", "T", "--scope", "tracked.txt"]) == 0

    assert "declares no scope" not in capsys.readouterr().err


def test_scope_warning_flags_an_empty_entry(tmp_path: Path) -> None:
    """An empty entry reaches the contract and matches nothing; say so."""

    from agentmarshal.journal.open_task import scope_warnings

    warnings = scope_warnings(tmp_path, [""])

    assert len(warnings) == 1
    assert "empty" in warnings[0]


def test_recorded_by_prefers_the_project_actors_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A declared actor id is more useful than a raw address."""

    from agentmarshal.journal.actors import resolve_recorded_by

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "Lead@Example.Invalid"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / ".agentmarshal").mkdir()
    (tmp_path / ".agentmarshal" / "project.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "actors": {"lead": {"git_identities": ["lead@example.invalid"]}},
            }
        ),
        encoding="utf-8",
    )

    assert resolve_recorded_by(tmp_path) == ("lead", "project-actor")


def test_recorded_by_falls_back_to_the_git_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agentmarshal.journal.actors import resolve_recorded_by

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "solo@example.invalid"],
        cwd=tmp_path,
        check=True,
    )

    assert resolve_recorded_by(tmp_path) == ("solo@example.invalid", "git-identity")


def test_recorded_by_override_marks_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An override that hid itself would defeat the field."""

    from agentmarshal.journal.actors import resolve_recorded_by

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "review-bot")

    assert resolve_recorded_by(tmp_path) == ("review-bot", "override")


def test_recorded_by_is_omitted_when_undeterminable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Absent beats guessed: the record stays valid without the pair."""

    from agentmarshal.journal import actors

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.setattr(actors, "_git_identity", lambda _root: None)

    assert actors.resolve_recorded_by(tmp_path) is None


def test_write_record_stamps_the_creating_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stamped centrally, so no record type is missed."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-agent")
    root = tmp_path / ".agentmarshal" / "journal"
    root.mkdir(parents=True)
    record = create_opened_record("CR-001", "1.0")

    write_record(root, "CR-001", record)

    stored = read_records(root, "CR-001")[0]
    assert stored["recorded_by"] == "an-agent"
    assert stored["recorded_by_source"] == "override"


def test_recorded_by_is_rejected_when_supplied_by_the_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Derived means derived: a supplied value would outrank the override."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-agent")
    root = tmp_path / ".agentmarshal" / "journal"
    root.mkdir(parents=True)
    record = create_opened_record("CR-001", "1.0") | {
        "recorded_by": "someone-else",
        "recorded_by_source": "override",
    }

    with pytest.raises(JournalRecordError, match="must not be supplied"):
        write_record(root, "CR-001", record)


def test_an_incoherent_recorded_by_pair_fails_validation(tmp_path: Path) -> None:
    """The check belongs on the shared path, so a hand-edited record is caught."""

    record = create_opened_record("CR-001", "1.0")
    record["recorded_by_source"] = "git-identity"  # no recorded_by beside it

    from agentmarshal.journal.records import validate_record_content

    with pytest.raises(JournalRecordError, match="recorded_by"):
        validate_record_content(
            "01J00000000000000000000000-opened.json", json.dumps(record)
        )


def test_actors_table_skips_an_empty_actor_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty id would resolve to an empty actor and write an invalid record."""

    from agentmarshal.journal.actors import resolve_recorded_by

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "x@example.invalid"], cwd=tmp_path, check=True
    )
    (tmp_path / ".agentmarshal").mkdir()
    (tmp_path / ".agentmarshal" / "project.json").write_text(
        json.dumps(
            {"schema": 1, "actors": {"": {"git_identities": ["x@example.invalid"]}}}
        ),
        encoding="utf-8",
    )

    assert resolve_recorded_by(tmp_path) == ("x@example.invalid", "git-identity")


def test_recorded_by_null_is_not_the_same_as_absent(tmp_path: Path) -> None:
    """A field present with a null value names no actor while looking like it does."""

    from agentmarshal.journal.records import validate_record_content

    record = create_opened_record("CR-001", "1.0")
    record["recorded_by"] = None
    record["recorded_by_source"] = None

    with pytest.raises(JournalRecordError, match="recorded_by"):
        validate_record_content(
            "01J00000000000000000000000-opened.json", json.dumps(record)
        )


def test_a_malformed_recorded_by_source_fails_closed(tmp_path: Path) -> None:
    """An unhashable value must be refused, not raise TypeError out of validation."""

    from agentmarshal.journal.records import validate_record_content

    record = create_opened_record("CR-001", "1.0")
    record["recorded_by"] = "someone"
    record["recorded_by_source"] = ["git-identity"]

    with pytest.raises(JournalRecordError, match="recorded_by_source"):
        validate_record_content(
            "01J00000000000000000000000-opened.json", json.dumps(record)
        )


def test_opened_record_uses_the_actors_table_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`open` writes through a staging dir; attribution must not differ for it."""

    from agentmarshal.cli import main

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "lead@example.invalid"], cwd=repo, check=True
    )
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["actors"] = {"lead": {"git_identities": ["lead@example.invalid"]}}
    project_file.write_text(json.dumps(data), encoding="utf-8")

    assert main(["open", "--title", "T", "--scope", "src/"]) == 0

    opened = read_records(repo / ".agentmarshal" / "journal", "CR-001")[0]
    assert opened["recorded_by"] == "lead"
    assert opened["recorded_by_source"] == "project-actor"


def test_find_git_root_refuses_a_non_utf8_path_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git permits non-UTF-8 path bytes; a decode error must not escape."""

    from agentmarshal import project as project_module

    class _Result:
        returncode = 0
        stdout = b"/tmp/\xff-repo"

    monkeypatch.setattr(
        "agentmarshal.project.subprocess.run", lambda *a, **k: _Result()
    )

    with pytest.raises(project_module.GitNotAvailableError, match="not valid UTF-8"):
        project_module.find_git_root(tmp_path)


def test_readback_catches_a_file_that_opens_but_cannot_be_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Opening can succeed on a file whose first read fails."""

    from agentmarshal import project as project_module

    class _Unreadable:
        def __enter__(self) -> _Unreadable:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self, size: int = -1) -> bytes:
            raise OSError(5, "Input/output error")

    target = tmp_path / "project.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(Path, "open", lambda *a, **k: _Unreadable())

    with pytest.raises(
        project_module.AgentMarshalProjectError, match="cannot read it back"
    ):
        project_module._assert_readable(target)


def test_init_reports_when_it_cannot_read_back_what_it_wrote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Writing without checking leaves the caller a path nobody can use."""

    from agentmarshal import project as project_module

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    def _unreadable(path: Path) -> None:
        raise project_module.AgentMarshalProjectError(
            f"wrote {path} but cannot read it back: simulated"
        )

    monkeypatch.setattr(project_module, "_assert_readable", _unreadable)

    with pytest.raises(
        project_module.AgentMarshalProjectError, match="cannot read it back"
    ):
        project_module.initialize_project(repo)


def test_open_fails_when_the_task_it_wrote_is_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adopter proposal 011: open reported success on a journal nobody could read."""

    from agentmarshal.cli import main
    from agentmarshal.journal import open_task as open_task_module

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0

    real_open: Any = Path.open

    def _deny_records(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self.suffix == ".json" and "records" in self.parts:
            raise PermissionError(13, "Permission denied")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _deny_records)

    with pytest.raises(open_task_module.TaskOpenError, match="cannot read it back"):
        open_task_module.open_task(repo, "T", ["src/"])


def test_init_scaffolds_the_upstream_outbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The convention arrives with the tool instead of having to be found."""

    from agentmarshal.cli import main

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)

    assert main(["init"]) == 0

    readme = repo / ".agentmarshal" / "upstream" / "README.md"
    assert readme.is_file()
    assert "Sanitize at source" in readme.read_text(encoding="utf-8")
    assert "upstream" in capsys.readouterr().out


def _host_snapshot(host: Path) -> dict[Path, bytes]:
    """Every file under the host, .git included."""

    return {
        path.relative_to(host): path.read_bytes()
        for path in host.rglob("*")
        if path.is_file()
    }


def test_full_sidecar_session_never_changes_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    init_git_repo(host)
    init_git_repo(sidecar)
    base = _commit_file(host, "app.txt", "one\n")
    head = _commit_file(host, "app.txt", "two\n")
    linked = tmp_path / "linked"
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "--quiet",
            "-b",
            "feat/CR-001-recorded",
            str(linked),
            "HEAD",
        ],
        cwd=host,
        check=True,
    )
    linked_app = linked / "app.txt"
    linked_stat = linked_app.stat()
    os.utime(
        linked_app,
        ns=(linked_stat.st_atime_ns, linked_stat.st_mtime_ns + 2_000_000_000),
    )
    reviewer = tmp_path / "reviewer.py"
    reviewer.write_text(
        """import json
import re
import sys
from pathlib import Path

prompt = sys.stdin.read()
assert Path("app.txt").read_text(encoding="utf-8") == "two\\n"
assert not Path(".git").exists()
commit = re.search(r"reviewed commit is ([0-9a-f]{40})", prompt).group(1)
print("AGENTMARSHAL_VERDICT_BEGIN")
verdict = {
    "reviewed_commit": commit,
    "verdict": "changes_required",
    "findings": ["F-1"],
}
print(json.dumps(verdict))
print("AGENTMARSHAL_VERDICT_END")
""",
        encoding="utf-8",
    )
    # .git is included deliberately. Excluding it tested the letter of
    # ADR-0008 Decision 3 while leaving its spirit unchecked: a host-side
    # 'git status' without --no-optional-locks rewrites .git/index, which is a
    # write into a repository we promise never to write to and which an
    # exclusion would hide.
    before_files = _host_snapshot(host)
    before_untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=host,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    monkeypatch.chdir(sidecar)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", f"{sys.executable} {reviewer}")

    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Private task", "--scope", "app.txt"]) == 0
    # app.txt exists in the host and not in the sidecar, so a scope check
    # against the wrong root would warn. Warnings go to stderr and never
    # change the exit code, so without this assertion the criterion could be
    # broken with the suite still green.
    assert "matches no path" not in capsys.readouterr().err
    assert main(["open", "--title", "Absent", "--scope", "not-in-host.txt"]) == 0
    assert "matches no path" in capsys.readouterr().err
    assert main(["abandon", "--task", "CR-002", "--reason", "probe"]) == 0
    assert main(["brief", "--task", "CR-001"]) == 0
    assert main(["amend", "--task", "CR-001", "--reason", "Clarify scope"]) == 0
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
                "reviewer",
                "--vendor",
                "test",
                "--model",
                "test",
                "--email",
                "reviewer@example.invalid",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "review",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--role",
                "reviewer",
                "--vendor",
                "test",
                "--model",
                "test",
                "--email",
                "reviewer@example.invalid",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "accept",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--by",
                "operator@example.invalid",
                "--reason",
                "Accepted for this private workflow",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "record-session",
                "--task",
                "CR-001",
                "--role",
                "implementer",
                "--actor",
                "operator",
                "--activity",
                "implementation",
                "--outcome",
                "done",
            ]
        )
        == 0
    )
    assert main(["status", "CR-001"]) == 0
    assert main(["report", "--task", "CR-001"]) == 0
    assert main(["validate"]) == 0
    # gate and complete issue the most host-side git of any command —
    # rev-parse, merge-base, diff, ls-tree, log, show — so they are the ones
    # that most need the index-skew probe this test carries. Recording the
    # completion through the command, rather than writing the record directly,
    # is what puts them inside the snapshot.
    # The skew above is on the linked worktree, whose index only a command
    # running inside it can refresh. gate and complete run git in the host
    # root, so its index needs the same treatment or their coverage here
    # probes nothing — checked by making the gate refresh it and watching this
    # test still pass without this line.
    host_app = host / "app.txt"
    host_stat = host_app.stat()
    os.utime(
        host_app, ns=(host_stat.st_atime_ns, host_stat.st_mtime_ns + 2_000_000_000)
    )
    monkeypatch.setenv("AGENTMARSHAL_PIPELINE_OK_SHA", head)
    assert main(["gate", "--task", "CR-001", "--commit", head, "--base", base]) == 0
    assert main(["complete", "--task", "CR-001", "--commit", head, "--base", base]) == 0
    assert main(["prune"]) == 0
    # Exit code alone passed while prune read task state from the host, which
    # has no journal, and called every task unknown. The report's content is
    # the thing under test.
    pruned = capsys.readouterr().out
    assert (
        f"eligible: {linked} "
        "(branch feat/CR-001-recorded; task CR-001 is done and clean)" in pruned
    )
    assert "unknown" not in pruned
    # F-2: reopen is named in the sidecar command list and was the one command
    # in it no test exercised there.
    assert main(["reopen", "--task", "CR-001", "--reason", "More to do"]) == 0
    assert main(["open", "--title", "Abandoned", "--scope", "app.txt"]) == 0
    assert main(["abandon", "--task", "CR-003", "--reason", "Superseded"]) == 0
    capsys.readouterr()

    after_files = _host_snapshot(host)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=host,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    after_untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=host,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert status == ""
    assert after_untracked == before_untracked
    assert after_files == before_files


def test_sidecar_refuses_authoritative_commands_and_host_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    init_git_repo(host)
    init_git_repo(sidecar)
    _commit_file(host, "app.txt", "one\n")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    capsys.readouterr()

    # CR-081 replaced the refusal this once asserted: a sidecar gate now runs
    # and advises. What must still hold is that a bare invocation is refused —
    # the host's branch names a task in the host's numbering, not this
    # journal's — and that the refusal does not borrow the authority's wording.
    assert main(["gate"]) == 1
    assert "--task is required in a sidecar" in capsys.readouterr().err
    assert (
        main(["complete", "--task", "CR-001", "--commit", "HEAD", "--base", "HEAD"])
        == 1
    )
    assert "could not evaluate this candidate" in capsys.readouterr().err
    assert main(["prune", "--delete"]) == 1
    assert (
        "host worktree and repository must remain read-only" in capsys.readouterr().err
    )


def test_missing_sidecar_host_fails_only_when_command_needs_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    init_git_repo(host)
    init_git_repo(sidecar)
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Task"]) == 0
    os.rename(host, tmp_path / "moved-host")
    capsys.readouterr()

    assert main(["status"]) == 0
    assert main(["status", "CR-001"]) == 0
    assert main(["open", "--title", "Another task"]) == 1
    error = capsys.readouterr().err
    assert str(host) in error
    assert "does not exist" in error
    assert "Traceback" not in error


def test_init_does_not_overwrite_an_outbox_readme(tmp_path: Path) -> None:
    """An adopter who wrote their own convention does not lose it."""

    from agentmarshal import project as project_module

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    outbox = repo / ".agentmarshal" / "upstream"
    outbox.mkdir(parents=True)
    (outbox / "README.md").write_text("ours", encoding="utf-8")

    initialized = project_module.initialize_project(repo)

    assert (outbox / "README.md").read_text(encoding="utf-8") == "ours"
    assert initialized.outbox_created


def test_init_succeeds_when_the_outbox_cannot_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A project that could not write a convenience is still a project."""

    from agentmarshal import project as project_module

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    real_mkdir = Path.mkdir

    def _refuse(self: Path, *args: Any, **kwargs: Any) -> None:
        if self.name == "upstream":
            raise OSError(13, "Permission denied")
        real_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", _refuse)

    initialized = project_module.initialize_project(repo)

    assert not initialized.outbox_created
    assert "Permission denied" in (initialized.outbox_error or "")
    assert (initialized.project_root / ".agentmarshal" / "project.json").is_file()


def test_init_states_the_convention_even_when_the_outbox_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Silence would leave the operator believing nothing was meant to happen."""

    from agentmarshal.cli import main

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    real_mkdir = Path.mkdir

    def _refuse(self: Path, *args: Any, **kwargs: Any) -> None:
        if self.name == "upstream":
            raise OSError(13, "Permission denied")
        real_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", _refuse)

    assert main(["init"]) == 0

    captured = capsys.readouterr()
    assert "Findings about AgentMarshal itself go in" in captured.out
    assert "could not create" in captured.err
    assert "Permission denied" in captured.err


def test_init_does_not_call_a_file_named_upstream_an_outbox(
    tmp_path: Path,
) -> None:
    """A path taken by a file leaves no directory and no README to use."""

    from agentmarshal import project as project_module

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    project_directory = repo / ".agentmarshal"
    project_directory.mkdir()
    (project_directory / "upstream").write_text("not a directory", encoding="utf-8")

    initialized = project_module.initialize_project(repo)

    assert not initialized.outbox_created
    assert not (project_directory / "upstream" / "README.md").exists()


def test_every_record_factory_writes_the_current_schema() -> None:
    """The guarantee is about what the tool writes, not what write_record accepts.

    write_record deliberately still persists an older record: constructing one
    is how backward reading is tested, and backward reading is what makes the
    schema bump safe. So the promise is pinned here, over the factories.
    """

    import inspect

    from agentmarshal.journal import records as records_module

    factories = [
        value
        for name, value in vars(records_module).items()
        if name.startswith("create_") and name.endswith("_record")
    ]
    assert factories, "no record factories found"
    for factory in factories:
        parameters = inspect.signature(factory).parameters
        arguments: list[object] = []
        for name, parameter in parameters.items():
            if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                continue
            if parameter.default is not inspect.Parameter.empty:
                continue
            arguments.append(_placeholder_for(name))
        expected = 4 if factory.__name__ == "create_finding_record" else 3
        assert factory(*arguments)["schema"] == expected, factory.__name__


def _placeholder_for(name: str) -> object:
    if name.endswith("_commit"):
        return "a" * 40
    if "findings" in name:
        return ["F-1"]
    if name == "artifacts":
        return [{"ref": "result.md", "hash": "a" * 64}]
    if "tokens" in name:
        return 0
    return {
        "task_id": "CR-001",
        "tool_version": "0.1.0",
        "verdict": "changes_required",
        "activity": "implementation",
    }.get(name, "value")


def test_a_session_is_recorded_when_the_cost_is_known(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A task's cost is known when it ends, and then the task is done.

    ADR-0005 Decision 3 admits sessions after a terminal record, the projection
    implements it, and the gate keeps a measurements-only lane for it — an
    open-only guard put that lane out of the CLI's reach.
    """

    repo = tmp_path / "repo"
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Done task", "--scope", "src/"]) == 0
    assert main(["open", "--title", "Abandoned task", "--scope", "src/"]) == 0
    journal = journal_root(repo)
    write_record(
        journal, "CR-001", create_completed_record("CR-001", "0.1.0", "a" * 40)
    )
    write_record(journal, "CR-002", create_abandoned_record("CR-002", "0.1.0", "no"))

    for task in ("CR-001", "CR-002"):
        assert (
            main(
                [
                    "record-session",
                    "--task",
                    task,
                    "--role",
                    "lead",
                    "--actor",
                    "operator",
                    "--activity",
                    "implementation",
                    "--outcome",
                    "success",
                    "--input-tokens",
                    "10",
                    "--output-tokens",
                    "5",
                    "--usage-provider",
                    "example",
                    "--usage-method",
                    "measured",
                ]
            )
            == 0
        )

    # The measurement changes no state: that is what makes it safe after a
    # terminal record, and it is the projection's job rather than this
    # command's.
    assert project_status(read_records(journal, "CR-001")) == "done"
    assert project_status(read_records(journal, "CR-002")) == "abandoned"


def test_record_session_still_refuses_an_unknown_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dropping the state guard must not drop the existence check."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0

    assert (
        main(
            [
                "record-session",
                "--task",
                "CR-999",
                "--role",
                "lead",
                "--actor",
                "operator",
                "--activity",
                "implementation",
                "--outcome",
                "success",
            ]
        )
        == 1
    )

    assert "unknown task id: CR-999" in capsys.readouterr().err


def test_record_session_still_refuses_an_invalid_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dropping the state guard must not drop record validation either.

    The criterion said validation is unchanged; that half was asserted and not
    demonstrated until here.
    """

    repo = tmp_path / "repo"
    init_git_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Task", "--scope", "src/"]) == 0

    assert (
        main(
            [
                "record-session",
                "--task",
                "CR-001",
                "--role",
                "lead",
                "--actor",
                "operator",
                "--activity",
                "bogus",
                "--outcome",
                "success",
            ]
        )
        == 1
    )

    assert "activity" in capsys.readouterr().err
