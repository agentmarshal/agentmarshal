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
    create_review_record,
    generate_ulid,
    parse_contract,
    project_status,
    read_records,
    write_record,
)
from agentmarshal.journal.open_task import TaskOpenError, journal_root, open_task


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
    assert read_records(root, "CR-001") == [record | {"id": identifier}]


def test_builders_emit_schema_2_with_live_provenance(tmp_path: Path) -> None:
    # Forward capture is in-toto-complete from the start: builders emit
    # schema 2 with live provenance, and the record round-trips through the
    # validating writer/reader.
    record = create_opened_record("CR-001", "1.0")
    assert record["schema"] == 2
    assert record["source"] == "live"

    review = create_review_record(
        "CR-001", "1.0", "a" * 40, "approved", "r", "v", "m", "r@t.i", []
    )
    assert review["schema"] == 2
    assert review["source"] == "live"

    root = tmp_path / "journal"
    identifier = "01J00000000000000000000000"
    write_record(root, "CR-001", record, record_id=identifier)
    assert read_records(root, "CR-001") == [record | {"id": identifier}]


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
    assert read_records(root, "CR-001") == [record | {"id": identifier}]


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


def test_scope_warning_mirrors_what_the_gate_can_match(tmp_path: Path) -> None:
    """git lists files, so the filesystem is not the right question to ask."""

    from agentmarshal.journal.open_task import scope_warnings

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "foo").write_text("x", encoding="utf-8")

    # 'foo/' matches the exact path 'foo' by the gate's rule, so it is silent
    # even though 'foo' is a file, not a directory.
    assert scope_warnings(tmp_path, ["foo/"]) == []
    # A plain entry naming a directory can never match: git emits file paths.
    assert len(scope_warnings(tmp_path, ["src"])) == 1


def test_scope_warning_rejects_paths_the_gate_can_never_see(tmp_path: Path) -> None:
    """Absolute, parent-escaping and dot-prefixed entries resolve but cannot match."""

    from agentmarshal.journal.open_task import scope_warnings

    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)

    warnings = scope_warnings(
        tmp_path, ["/etc/", "../outside/", "./README.md", "src/../README.md", "/"]
    )

    assert len(warnings) == 5
    assert all(
        "not a repository-relative path" in warning or "matches nothing" in warning
        for warning in warnings
    )


def test_scope_warning_stays_silent_when_entries_match(tmp_path: Path) -> None:
    from agentmarshal.journal.open_task import scope_warnings

    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("x", encoding="utf-8")

    assert scope_warnings(tmp_path, ["src/", "README.md"]) == []


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


def test_scope_warning_flags_an_empty_entry(tmp_path: Path) -> None:
    """An empty entry reaches the contract and matches nothing; say so."""

    from agentmarshal.journal.open_task import scope_warnings

    warnings = scope_warnings(tmp_path, ["", "   "])

    assert len(warnings) == 2
    assert all("empty" in warning for warning in warnings)
