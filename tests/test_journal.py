"""Tests for journal contracts, records, and task opening."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import (
    JournalContractError,
    create_opened_record,
    generate_ulid,
    parse_contract,
    read_records,
    write_record,
)
from agentmarshal.journal.open_task import journal_root


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
