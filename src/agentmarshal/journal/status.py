"""Task status projections derived from journal evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.contracts import ContractHeader, parse_contract
from agentmarshal.journal.records import (
    JournalRecordError,
    ensure_journal_root_is_real,
    read_records,
    validate_task_id,
)

_RECORD_TYPE_STATES: Mapping[str, str | None] = {
    "opened": "open",
    "review": None,
    "session": None,
    "completed": "done",
    "abandoned": "abandoned",
}
_TERMINAL_RECORD_TYPES = frozenset({"completed", "abandoned"})


class TaskStatusError(ValueError):
    """Raised when task status cannot be safely projected."""


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
        # record. Any other record type after a terminal one is a
        # lifecycle mutation of a closed task and stays forbidden.
        if has_terminal_record and record_type != "session":
            raise TaskStatusError(
                "task has a lifecycle record after a terminal record"
            )
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
            f"contract id does not match its task directory: {task_directory / 'contract.md'}"
        )
    return TaskStatus(task_id, contract, records, project_status(records))


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
