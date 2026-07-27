"""Tests for the journal-wide validate command (CR-018)."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import generate_ulid
from agentmarshal.journal.validate import validate_journal


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tasks: int = 2) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    for index in range(tasks):
        assert main(["open", "--title", f"Task {index}", "--scope", "src/"]) == 0
    return repo


def _records_dir(repo: Path, task_id: str) -> Path:
    return repo / ".agentmarshal" / "journal" / "tasks" / task_id / "records"


def _opened_file(repo: Path, task_id: str) -> Path:
    return next(_records_dir(repo, task_id).glob("*-opened.json"))


def test_validate_passes_clean_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch, tasks=2)

    report = validate_journal(repo)

    assert report.passed, report.lines
    assert any("OK: CR-001" in line for line in report.lines)
    assert any("OK: CR-002" in line for line in report.lines)


def test_validate_empty_journal_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch, tasks=0)

    report = validate_journal(repo)

    assert report.passed, report.lines


def test_validate_reports_malformed_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch, tasks=1)
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text("not a valid contract header\n", encoding="utf-8")

    report = validate_journal(repo)

    assert not report.passed
    assert any("FAIL: CR-001" in line for line in report.lines)


def test_validate_reports_invalid_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch, tasks=1)
    _opened_file(repo, "CR-001").write_text("{ not json", encoding="utf-8")

    report = validate_journal(repo)

    assert not report.passed
    assert any("FAIL: CR-001" in line for line in report.lines)


def test_validate_reports_inconsistent_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A second opened record makes the projection ambiguous.
    repo = _project(tmp_path, monkeypatch, tasks=1)
    opened = _opened_file(repo, "CR-001")
    duplicate = _records_dir(repo, "CR-001") / f"{generate_ulid()}-opened.json"
    duplicate.write_text(opened.read_text(encoding="utf-8"), encoding="utf-8")

    report = validate_journal(repo)

    assert not report.passed
    assert any("FAIL: CR-001" in line for line in report.lines)


def test_validate_reports_record_id_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # CR-002's record reuses CR-001's record id (same id, different task).
    repo = _project(tmp_path, monkeypatch, tasks=2)
    shared_id = _opened_file(repo, "CR-001").name.split("-", 1)[0]
    other = _opened_file(repo, "CR-002")
    other.rename(other.parent / f"{shared_id}-opened.json")

    report = validate_journal(repo)

    assert not report.passed
    assert any("also used by" in line for line in report.lines)


def test_validate_reports_non_utf8_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch, tasks=1)
    _opened_file(repo, "CR-001").write_bytes(b"\xff\xfe not utf-8")

    report = validate_journal(repo)

    assert not report.passed
    assert any("FAIL: CR-001" in line for line in report.lines)


def test_validate_fails_on_symlinked_journal_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A journal root reached through a symlink must fail closed, not slip
    # past the early "no tasks" return.
    repo = _project(tmp_path, monkeypatch, tasks=1)
    journal = repo / ".agentmarshal" / "journal"
    real = repo / ".agentmarshal" / "journal_real"
    journal.rename(real)
    journal.symlink_to(real)

    report = validate_journal(repo)

    assert not report.passed
    assert any("journal root is not valid" in line for line in report.lines)


def test_validate_fails_closed_on_unreadable_tasks_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An enumeration failure is a controlled FAIL, never a traceback.
    repo = _project(tmp_path, monkeypatch, tasks=1)

    original_iterdir = Path.iterdir

    def boom(self: Path):  # type: ignore[no-untyped-def]
        if self.name == "tasks":
            raise PermissionError("tasks directory is unreadable")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", boom)

    report = validate_journal(repo)

    assert not report.passed
    assert any("cannot read tasks directory" in line for line in report.lines)


def test_validate_cli_fails_outside_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["validate"]) == 1
    assert "initialized project" in capsys.readouterr().err


def test_validate_cli_passes_clean_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, monkeypatch, tasks=2)

    assert main(["validate"]) == 0
    assert "validate: passed" in capsys.readouterr().out
