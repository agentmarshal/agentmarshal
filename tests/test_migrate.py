"""Tests for v1 journal migration."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.status import load_task_status
from agentmarshal.migrate import JournalMigrationError, migrate_journal


def write_task(
    root: Path,
    location: str,
    task_id: str,
    status: str,
    *,
    extra_headers: str = "",
) -> Path:
    path = root / "tasks" / location / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {task_id}: Migrated task\n\n"
        f"Owner: lead\nType: feat\nCreated: 2026-07-26\nStatus: {status}\n"
        f"{extra_headers}Scope:\n- src/agentmarshal/\n- tests/\n\n"
        "## Context\n\nTask body.\n",
        encoding="utf-8",
    )
    return path


def write_review(
    root: Path,
    filename: str,
    task_id: str,
    verdict: str,
    findings: str,
) -> Path:
    path = root / "reviews" / "2026" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"Task: {task_id}\nReviewer-Role: qa\nReviewer-Vendor: codex\n"
        "Reviewer-Model: test-model\nReviewer-Email: qa@example.invalid\n"
        f"Reviewed-Commit: {'a' * 40}\nVerdict: {verdict}\n"
        f"Finding-IDs: {findings}\n\nReview body.\n",
        encoding="utf-8",
    )
    return path


def test_migrate_journal_converts_lifecycle_states(tmp_path: Path) -> None:
    source = tmp_path / "v1"
    target = tmp_path / "v2"
    write_task(
        source,
        "done/2026",
        "CR-001",
        "done",
        extra_headers=f"Merged-Commit: {'b' * 40}\n",
    )
    write_task(
        source, "abandoned", "CR-002", "abandoned", extra_headers="Reason: superseded\n"
    )
    write_task(source, "open", "CR-003", "open")
    write_review(source, "CR-001-approved.md", "CR-001", "approved", "none")
    write_review(source, "CR-003-changes.md", "CR-003", "changes_required", "F-001")

    summaries = migrate_journal(source, target)

    assert summaries == [
        "CR-001: done (1 review(s))",
        "CR-002: abandoned (0 review(s))",
        "CR-003: open (1 review(s))",
    ]
    assert load_task_status(target, "CR-001").state == "done"
    assert load_task_status(target, "CR-002").state == "abandoned"
    open_task = load_task_status(target, "CR-003")
    assert open_task.state == "open"
    assert open_task.contract.scope == ("src/agentmarshal/", "tests/")
    assert open_task.records[1]["verdict"] == "changes_required"


def test_migrate_journal_cli_preserves_source_and_refuses_nonempty_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "v1"
    target = tmp_path / "v2"
    task_path = write_task(source, "open", "CR-001", "in_review")
    source_content = task_path.read_bytes()

    assert (
        main(["migrate-journal", "--source", str(source), "--target", str(target)]) == 0
    )
    assert task_path.read_bytes() == source_content
    assert "CR-001: open" in capsys.readouterr().out
    assert (
        main(["migrate-journal", "--source", str(source), "--target", str(target)]) == 1
    )
    assert "target journal already exists" in capsys.readouterr().err


def test_migrate_journal_refuses_target_inside_source(tmp_path: Path) -> None:
    source = tmp_path / "v1"
    target = source / "migrated"
    write_task(source, "open", "CR-001", "open")

    with pytest.raises(JournalMigrationError, match="must not be inside"):
        migrate_journal(source, target)

    assert not target.exists()


def test_migrate_journal_removes_staging_when_later_task_fails(tmp_path: Path) -> None:
    source = tmp_path / "v1"
    target = tmp_path / "v2"
    write_task(source, "open", "CR-001", "open")
    write_task(source, "done/2026", "CR-002", "done")

    with pytest.raises(JournalMigrationError, match="no Merged-Commit"):
        migrate_journal(source, target)

    assert not target.exists()


@pytest.mark.parametrize(
    ("task_content", "review", "error"),
    [
        (
            "# CR-001: Migrated task\n\nOwner lead\n",
            None,
            "malformed Key: Value header",
        ),
        (None, None, "unknown Status: unexpected"),
        (None, ("CR-001", "approved", "F-001"), "inconsistent"),
        (None, ("CR-999", "approved", "none"), "unknown task"),
    ],
)
def test_migrate_journal_fails_closed(
    tmp_path: Path,
    task_content: str | None,
    review: tuple[str, str, str] | None,
    error: str,
) -> None:
    source = tmp_path / "v1"
    target = tmp_path / "v2"
    task_path = write_task(source, "open", "CR-001", "open")
    if task_content is not None:
        task_path.write_text(task_content, encoding="utf-8")
    elif error.startswith("unknown Status"):
        task_path.write_text(
            task_path.read_text(encoding="utf-8").replace(
                "Status: open", "Status: unexpected"
            ),
            encoding="utf-8",
        )
    if review is not None:
        write_review(source, "review.md", *review)

    with pytest.raises(JournalMigrationError, match=error):
        migrate_journal(source, target)

    assert not target.exists()
