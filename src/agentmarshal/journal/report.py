"""Delegation economics projected from append-only journal records."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal.journal.records import JournalRecordError
from agentmarshal.journal.status import (
    TaskStatus,
    TaskStatusError,
    list_task_statuses,
    load_task_status,
)


class ReportError(Exception):
    """Raised when journal measurements cannot be safely reported."""


@dataclass(frozen=True)
class TaskReport:
    """Measured work and terminal status for one task."""

    task_id: str
    state: str
    review_cycles: int
    tokens: int
    usage_provenance: str | None = None
    decision: str | None = None


@dataclass(frozen=True)
class JournalReport:
    """Task-level measurements and their aggregate totals."""

    tasks: tuple[TaskReport, ...]
    review_cycles: int
    tokens: int
    usage_provenance: str | None = None


def _usage_provenance(records: Iterable[dict[str, object]]) -> str | None:
    methods = {
        cast(dict[str, str], record["usage"])["method"]
        if "usage" in record
        else "unrecorded"
        for record in records
        if record["record_type"] == "session"
    }
    if not methods:
        return None
    if len(methods) == 1:
        return methods.pop()
    return "mixed"


def _task_report(status: TaskStatus) -> TaskReport:
    records = status.records
    review_cycles = sum(record["record_type"] == "review" for record in records)
    tokens = sum(
        sum(cast(dict[str, int], record["tokens"]).values())
        for record in records
        if record["record_type"] == "session"
    )
    decision = None
    if any(record["record_type"] == "acceptance" for record in records):
        decision = "accepted-over-findings"
    else:
        completed = next(
            (
                record
                for record in reversed(records)
                if record["record_type"] == "completed"
            ),
            None,
        )
        if completed is not None:
            binding = (
                ("reviewed_finding", completed["completed_finding"])
                if "completed_finding" in completed
                else ("reviewed_commit", completed["completed_commit"])
            )
            reviews = [
                record
                for record in records
                if record["record_type"] == "review"
                and record.get(binding[0]) == binding[1]
            ]
            if reviews and reviews[-1]["verdict"] == "approved":
                decision = "approved"
    return TaskReport(
        status.task_id,
        status.state,
        review_cycles,
        tokens,
        _usage_provenance(records),
        decision,
    )


def build_report(journal_root: Path, task_id: str | None = None) -> JournalReport:
    """Read journal evidence and derive per-task delegation economics."""

    try:
        # A task-scoped report must not scan or validate unrelated tasks
        # (ADR-0004: reading one task never requires scanning the journal).
        if task_id is not None:
            statuses = [load_task_status(journal_root, task_id)]
        else:
            statuses = list_task_statuses(journal_root)
        tasks = tuple(_task_report(status) for status in statuses)
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReportError(str(error)) from error
    return JournalReport(
        tasks,
        sum(task.review_cycles for task in tasks),
        sum(task.tokens for task in tasks),
        _usage_provenance([record for status in statuses for record in status.records]),
    )


def format_report(
    report: JournalReport, *, include_summary: bool = True
) -> tuple[str, ...]:
    """Return stable, tab-separated report lines for CLI output."""

    lines = []
    for task in report.tasks:
        line = (
            f"{task.task_id}\t{task.state}\treviews={task.review_cycles}"
            f"\ttokens={task.tokens}"
        )
        if task.usage_provenance is not None:
            line += f"\tusage={task.usage_provenance}"
        if task.decision is not None:
            line += f"\tdecision={task.decision}"
        lines.append(line)
    if not include_summary:
        return tuple(lines)
    state_counts: dict[str, int] = {}
    for task in report.tasks:
        state_counts[task.state] = state_counts.get(task.state, 0) + 1
    state_summary = " ".join(
        f"{state}={count}" for state, count in sorted(state_counts.items())
    )
    summary = (
        f"Summary\t{state_summary}\treviews={report.review_cycles}"
        f"\ttokens={report.tokens}"
    )
    if report.usage_provenance is not None:
        summary += f"\tusage={report.usage_provenance}"
    lines.append(summary)
    return tuple(lines)
