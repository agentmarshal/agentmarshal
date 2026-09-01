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
    *,
    usage_provider: str | None = None,
    usage_method: str | None = None,
) -> Path:
    """Validate and append an attributed session to a task in any state.

    Deliberately not restricted to open tasks. A task's cost is known when it
    ends, and at that moment the task is ``done`` — an open-only guard put the
    one honest moment out of reach, which is why this project recorded no live
    session in forty-eight consecutive tasks and why adopter proposal 008
    described reconstructing usage "afterwards".

    Nothing about state is weakened by allowing it: a session projects to no
    state (ADR-0005 Decision 3), ``project_status`` already admits one after a
    terminal record, and the gate keeps a measurements-only lane requiring a
    strictly additive candidate confined to the task's own records. Those are
    the checks that make this safe, and this function is not one of them.
    """

    try:
        load_task_status(journal_root, task_id)
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
            usage_provider=usage_provider,
            usage_method=usage_method,
        )
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise SessionRecordError(str(error)) from error
