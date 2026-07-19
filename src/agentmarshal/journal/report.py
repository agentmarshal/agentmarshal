"""Delegation economics projected from append-only journal records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from pathlib import Path

from agentmarshal.journal.records import JournalRecordError
from agentmarshal.journal.status import TaskStatus, TaskStatusError, list_task_statuses


class ReportError(Exception):
    """Raised when journal measurements cannot be safely reported."""


@dataclass(frozen=True)
class TaskReport:
    """Measured work and terminal status for one task."""

    task_id: str
    state: str
    review_cycles: int
    tokens: int


@dataclass(frozen=True)
class JournalReport:
    """Task-level measurements and their aggregate totals."""

    tasks: tuple[TaskReport, ...]
    review_cycles: int
    tokens: int


def _task_report(status: TaskStatus) -> TaskReport:
    records = status.records
    review_cycles = sum(record["record_type"] == "review" for record in records)
    tokens = sum(
        sum(cast(dict[str, int], record["tokens"]).values())
        for record in records
        if record["record_type"] == "session"
    )
    return TaskReport(status.task_id, status.state, review_cycles, tokens)


def build_report(journal_root: Path, task_id: str | None = None) -> JournalReport:
    """Read journal evidence and derive per-task delegation economics."""

    try:
        statuses = list_task_statuses(journal_root)
        if task_id is not None:
            statuses = [status for status in statuses if status.task_id == task_id]
            if not statuses:
                raise ReportError(f"unknown task id: {task_id}")
        tasks = tuple(
            _task_report(status) for status in statuses
        )
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReportError(str(error)) from error
    return JournalReport(
        tasks,
        sum(task.review_cycles for task in tasks),
        sum(task.tokens for task in tasks),
    )


def format_report(
    report: JournalReport, *, include_summary: bool = True
) -> tuple[str, ...]:
    """Return stable, tab-separated report lines for CLI output."""

    lines = [
        f"{task.task_id}\t{task.state}\treviews={task.review_cycles}\ttokens={task.tokens}"
        for task in report.tasks
    ]
    if not include_summary:
        return tuple(lines)
    state_counts: dict[str, int] = {}
    for task in report.tasks:
        state_counts[task.state] = state_counts.get(task.state, 0) + 1
    state_summary = " ".join(
        f"{state}={count}" for state, count in sorted(state_counts.items())
    )
    lines.append(
        f"Summary\t{state_summary}\treviews={report.review_cycles}\ttokens={report.tokens}"
    )
    return tuple(lines)
