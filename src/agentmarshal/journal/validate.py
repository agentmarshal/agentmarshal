"""Journal-wide integrity validation.

A deterministic, read-only aggregator: it composes the existing
validators (contract parsing, record schema validation, status
projection) across every task and reports every violation rather than
stopping at the first, so a governance CI job can assert the whole
journal is well-formed on each push. It adds no new policy of its own
beyond checking that record ids do not collide across tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.contracts import JournalContractError
from agentmarshal.journal.open_task import journal_root
from agentmarshal.journal.records import (
    JournalRecordError,
    ensure_journal_root_is_real,
    validate_task_id,
)
from agentmarshal.journal.status import (
    TaskStatusError,
    load_task_status,
)

# Errors from any composed validator are controlled refusals; a non-UTF-8
# or unreadable file must read as a failure line, never a traceback.
_VALIDATION_ERRORS = (
    TaskStatusError,
    JournalRecordError,
    JournalContractError,
    UnicodeDecodeError,
    OSError,
)


@dataclass(frozen=True)
class ValidationReport:
    """The outcome of a journal-wide validation."""

    passed: bool
    lines: list[str]


def _task_sort_key(task_id: str) -> tuple[int, str]:
    try:
        return (int(task_id.removeprefix("CR-")), task_id)
    except ValueError:
        return (1 << 30, task_id)


def validate_journal(project_root: Path) -> ValidationReport:
    """Validate every task in the journal, reporting each violation."""

    root = journal_root(project_root)
    # Reject a symlinked journal root before any other check, so a
    # redirected journal fails closed instead of slipping past an early
    # "no tasks" return.
    try:
        ensure_journal_root_is_real(root)
    except (JournalRecordError, OSError) as error:
        return ValidationReport(False, [f"FAIL: journal root is not valid: {error}"])

    tasks_directory = root / "tasks"
    try:
        if tasks_directory.is_symlink() or (
            tasks_directory.exists() and not tasks_directory.is_dir()
        ):
            return ValidationReport(
                False, [f"FAIL: task path is not a directory: {tasks_directory}"]
            )
        if not tasks_directory.exists():
            return ValidationReport(True, ["OK: no tasks to validate"])
        entries = sorted(tasks_directory.iterdir(), key=lambda path: path.name)
    except OSError as error:
        return ValidationReport(False, [f"FAIL: cannot read tasks directory: {error}"])

    lines: list[str] = []
    passed = True

    task_ids: list[str] = []
    for entry in entries:
        try:
            malformed_entry = entry.is_symlink() or not entry.is_dir()
        except OSError as error:
            lines.append(f"FAIL: {entry.name}: {error}")
            passed = False
            continue
        if malformed_entry:
            lines.append(f"FAIL: {entry.name}: task path is not a directory")
            passed = False
            continue
        try:
            validate_task_id(entry.name)
        except JournalRecordError as error:
            lines.append(f"FAIL: {entry.name}: invalid task id ({error})")
            passed = False
            continue
        task_ids.append(entry.name)

    seen_record_ids: dict[str, str] = {}
    for task_id in sorted(task_ids, key=_task_sort_key):
        try:
            status = load_task_status(root, task_id)
        except _VALIDATION_ERRORS as error:
            lines.append(f"FAIL: {task_id}: {error}")
            passed = False
            continue
        collision = False
        for record in status.records:
            record_id = record.get("id")
            if not isinstance(record_id, str):
                continue
            owner = seen_record_ids.get(record_id)
            if owner is not None:
                lines.append(
                    f"FAIL: {task_id}: record id {record_id} also used by {owner}"
                )
                passed = False
                collision = True
            else:
                seen_record_ids[record_id] = task_id
        if not collision:
            lines.append(
                f"OK: {task_id} ({status.state}, {len(status.records)} records)"
            )

    return ValidationReport(passed, lines)
