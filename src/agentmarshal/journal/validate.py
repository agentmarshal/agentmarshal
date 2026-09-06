"""Journal-wide integrity validation.

A deterministic, read-only aggregator: it composes the existing
validators (contract parsing, record schema validation, status
projection) across every task and reports every violation rather than
stopping at the first, so a governance CI job can assert the whole
journal is well-formed on each push. It adds no new policy of its own
beyond checking that record ids do not collide across tasks.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

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


def _review_artifact_failures(
    project_root: Path, task_id: str, records: tuple[dict[str, object], ...]
) -> list[str]:
    """Return failures for local artifacts pinned by review records."""

    failures: list[str] = []
    expected_root = PurePosixPath(
        ".agentmarshal", "journal", "tasks", task_id, "artifacts"
    )
    for record in records:
        if record["record_type"] != "review" or "artifacts" not in record:
            continue
        record_id = cast(str, record["id"])
        for artifact in cast(list[dict[str, str]], record["artifacts"]):
            reference = artifact["ref"]
            ref_path = PurePosixPath(reference)
            try:
                relative = ref_path.relative_to(expected_root)
            except ValueError:
                relative = PurePosixPath()
            if ref_path.is_absolute() or not relative.parts or ".." in ref_path.parts:
                failures.append(
                    f"review record {record_id} artifact {reference} is not under "
                    f"{expected_root.as_posix()}/"
                )
                continue
            path = project_root.joinpath(*ref_path.parts)
            try:
                resolved = path.resolve(strict=True)
            except FileNotFoundError:
                failures.append(
                    f"review record {record_id} artifact {reference} is missing"
                )
                continue
            except (OSError, RuntimeError) as error:
                failures.append(
                    f"review record {record_id} artifact {reference} cannot be "
                    f"resolved: {error}"
                )
                continue
            # A symlink anywhere between the project root and the file — the
            # artifacts directory included — would let bytes outside the
            # journal pass as its evidence: the resolved path must be the
            # lexical one, and a file.
            lexical = project_root.resolve().joinpath(*ref_path.parts)
            if resolved != lexical or not resolved.is_file():
                failures.append(
                    f"review record {record_id} artifact {reference} is reached "
                    "through a symlink or is not a file"
                )
                continue
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as error:
                failures.append(
                    f"review record {record_id} artifact {reference} cannot be read: "
                    f"{error}"
                )
                continue
            if digest != artifact["hash"]:
                failures.append(
                    f"review record {record_id} artifact {reference} does not match "
                    "its recorded sha256"
                )
    return failures


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
        artifact_failures = _review_artifact_failures(
            project_root, task_id, status.records
        )
        for failure in artifact_failures:
            lines.append(f"FAIL: {task_id}: {failure}")
            passed = False
        if not collision and not artifact_failures:
            lines.append(
                f"OK: {task_id} ({status.state}, {len(status.records)} records)"
            )

    return ValidationReport(passed, lines)
