"""Task status projections derived from journal evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentmarshal.journal.attestation import RECORD_TYPES
from agentmarshal.journal.contracts import ContractHeader, parse_contract
from agentmarshal.journal.records import (
    JournalRecordError,
    ensure_journal_root_is_real,
    read_records,
    validate_task_id,
)

# The record types a writer may ask the guard about, as a type rather than a
# string: mypy refuses a typo at the call site, and the guard's own runtime
# refusal then covers only a caller outside this package. A Literal cannot
# be derived from the registry at type-check time, so the names are written
# out here and a test pins them equal to the registry's writable types.
WritableRecordType = Literal[
    "opened",
    "review",
    "acceptance",
    "session",
    "amendment",
    "finding",
    "completed",
    "abandoned",
    "reopened",
    "check",
    "acknowledgement",
]

# The projection's tables are views over the one record-type registry in
# attestation.py — the state a type projects to, the types whose projected
# state is terminal, and the types admitted after a terminal record.
_RECORD_TYPE_STATES: Mapping[str, str | None] = {
    record_type: spec.projects_to for record_type, spec in RECORD_TYPES.items()
}
_TERMINAL_STATES = frozenset({"done", "abandoned"})
_TERMINAL_RECORD_TYPES = frozenset(
    record_type
    for record_type, spec in RECORD_TYPES.items()
    if spec.projects_to in _TERMINAL_STATES
)
_RECORD_TYPES_ADMITTED_AFTER_TERMINAL = frozenset(
    record_type
    for record_type, spec in RECORD_TYPES.items()
    if spec.admitted_after_terminal
)
# The types a writer may create — read here by the record guard and in
# records.py by the write path itself, so a type declared not writable
# cannot be written by naming it, however it reached the call site.
_WRITABLE_RECORD_TYPES = frozenset(
    record_type for record_type, spec in RECORD_TYPES.items() if spec.writable
)


class TaskStatusError(ValueError):
    """Raised when task status cannot be safely projected."""


def record_type_is_admitted_after_terminal(
    record_type: str, terminal_state: str
) -> bool:
    """Return whether the projection admits a record after ``terminal_state``.

    Measurements follow either terminal state. A reopening follows completion
    only, because it returns that state to open; abandonment remains terminal.
    """

    if record_type not in _RECORD_TYPES_ADMITTED_AFTER_TERMINAL:
        return False
    return terminal_state in RECORD_TYPES[record_type].admitted_after_terminal


def projected_state_of(record_type: str) -> str | None:
    """Return the state a record of *record_type* projects to, if any.

    The gate names lifecycle records by file name and asks here what they mean,
    instead of keeping a suffix-to-state table of its own.
    """

    return _RECORD_TYPE_STATES.get(record_type)


@dataclass(frozen=True)
class TaskStatus:
    """A task contract, its evidence, and the derived lifecycle state."""

    task_id: str
    contract: ContractHeader
    records: tuple[dict[str, object], ...]
    state: str


def project_status(records: Sequence[Mapping[str, object]]) -> str:
    """Derive a task state from validated records in their stored order."""

    state: str | None = None
    has_opened_record = False
    has_terminal_record = False
    for record in records:
        record_type = record.get("record_type")
        if not isinstance(record_type, str) or record_type not in _RECORD_TYPE_STATES:
            raise TaskStatusError(f"record has no status projection: {record_type!r}")
        # Measurements are not lifecycle (ADR-0005 Decision 3): a session
        # record projects to no state and may accrue after a terminal
        # record. Reopening is the sole lifecycle mutation admitted after
        # completion; all work records remain forbidden until it occurs.
        # One rule for what follows a terminal record, read here and by the
        # gate. A terminal record always sets `state`, so the fallback to ""
        # is never taken while `has_terminal_record` holds.
        if has_terminal_record and not record_type_is_admitted_after_terminal(
            record_type, state or ""
        ):
            if record_type == "reopened":
                raise TaskStatusError("an abandoned task cannot be reopened")
            raise TaskStatusError("task has a lifecycle record after a terminal record")
        if record_type == "reopened":
            if not has_terminal_record:
                raise TaskStatusError("task has a reopened record while it is open")
            has_terminal_record = False
        if record_type == "opened":
            if has_opened_record:
                raise TaskStatusError("task records contain multiple opened records")
            has_opened_record = True
        if record_type in _TERMINAL_RECORD_TYPES:
            has_terminal_record = True
        record_state = _RECORD_TYPE_STATES[record_type]
        if record_state is not None:
            state = record_state
    if not has_opened_record or state is None:
        raise TaskStatusError("task records do not contain an opened record")
    return state


def load_task_status(journal_root: Path, task_id: str) -> TaskStatus:
    """Load a task's validated journal data and project its current state."""

    try:
        validate_task_id(task_id)
    except JournalRecordError as error:
        raise TaskStatusError(str(error)) from error
    task_directory = journal_root / "tasks" / task_id
    records = tuple(read_records(journal_root, task_id))
    if not task_directory.is_dir() or task_directory.is_symlink():
        raise TaskStatusError(f"unknown task id: {task_id}")
    contract = parse_contract(task_directory / "contract.md")
    if contract.id != task_id:
        raise TaskStatusError(
            "contract id does not match its task directory: "
            f"{task_directory / 'contract.md'}"
        )
    return TaskStatus(task_id, contract, records, project_status(records))


def load_task_for_record(
    journal_root: Path, task_id: str, record_type: WritableRecordType
) -> TaskStatus:
    """Load a task and refuse a record its terminal projection cannot admit."""

    if record_type not in _WRITABLE_RECORD_TYPES:
        # An unknown type would silently fall on the refusing side, and a typo
        # towards "session" would start refusing the cost step of a completed
        # task. The registry's writable flag decides what a writer may write.
        raise TaskStatusError(f"unknown record type: {record_type!r}")
    task = load_task_status(journal_root, task_id)
    if task.state == "open":
        if record_type == "reopened":
            raise TaskStatusError(
                f"task {task_id} cannot be reopened (state: {task.state})"
            )
        return task
    if not record_type_is_admitted_after_terminal(record_type, task.state):
        if record_type == "reopened":
            raise TaskStatusError(
                f"task {task_id} cannot be reopened (state: {task.state})"
            )
        admitted = (
            "a measurement or a reopening" if task.state == "done" else "a measurement"
        )
        raise TaskStatusError(
            f"task {task_id} is not open (state: {task.state}); "
            f"its terminal record admits only {admitted}"
        )
    return task


def list_task_statuses(journal_root: Path) -> list[TaskStatus]:
    """Load all task statuses ordered by their canonical identifiers."""

    ensure_journal_root_is_real(journal_root)
    tasks_directory = journal_root / "tasks"
    if not tasks_directory.exists():
        return []
    if tasks_directory.is_symlink() or not tasks_directory.is_dir():
        raise TaskStatusError(f"task path is not a directory: {tasks_directory}")
    task_ids: list[str] = []
    for path in tasks_directory.iterdir():
        if path.is_symlink() or not path.is_dir():
            raise TaskStatusError(f"task path is not a directory: {path}")
        try:
            validate_task_id(path.name)
        except JournalRecordError as error:
            raise TaskStatusError(f"invalid task directory: {path}") from error
        task_ids.append(path.name)
    return [
        load_task_status(journal_root, task_id)
        for task_id in sorted(
            task_ids, key=lambda task_id: int(task_id.removeprefix("CR-"))
        )
    ]
