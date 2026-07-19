"""Tests for journal contracts, records, and task opening."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import (
    JournalContractError,
    JournalRecordError,
    create_opened_record,
    generate_ulid,
    parse_contract,
    read_records,
    write_record,
)
from agentmarshal.journal.open_task import TaskOpenError, journal_root, open_task


def init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )


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
    assert read_records(root, "CR-001") == [record]


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
