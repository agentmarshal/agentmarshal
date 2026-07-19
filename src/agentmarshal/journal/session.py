"""Trusted recording path for attributed task work sessions."""

from __future__ import annotations

from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.records import (
    JournalRecordError,
    create_session_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status


class SessionRecordError(Exception):
    """Raised when a work session cannot be recorded."""


def record_session(
    journal_root: Path,
    task_id: str,
    role: str,
    actor: str,
    activity: str,
    outcome: str,
    input_tokens: int,
    output_tokens: int,
    cache_tokens: int,
) -> Path:
    """Validate and append an attributed session against an open task."""

    try:
        task = load_task_status(journal_root, task_id)
        if task.state != "open":
            raise SessionRecordError(f"task {task_id} is not open (state: {task.state})")
        record = create_session_record(
            task_id,
            __version__,
            role,
            actor,
            activity,
            outcome,
            input_tokens,
            output_tokens,
            cache_tokens,
        )
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise SessionRecordError(str(error)) from error
