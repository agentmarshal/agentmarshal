"""Terminal lifecycle transactions: completion and abandonment.

Completion is automated on a passing merge: ``complete`` runs the gate
itself and records completion only when the gate passes (founding brief;
ADR-0004 keeps state a projection, so completion is an append-only
record, not a directory move).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.gate import (
    GateError,
    GateReport,
    run_findings_gate,
    run_gate,
)
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_completed_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status


class LifecycleError(Exception):
    """Raised when a terminal lifecycle transaction cannot be recorded."""


@dataclass(frozen=True)
class CompletionResult:
    """The gate report and, on success, the completion record path."""

    report: GateReport
    record_path: Path | None


def complete_task(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    pipeline_sha: str | None,
) -> CompletionResult:
    """Gate the candidate and record completion only when the gate passes."""

    journal_root = project_root / ".agentmarshal" / "journal"
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    if task.state != "open":
        raise LifecycleError(f"task {task_id} is not open (state: {task.state})")
    try:
        report = run_gate(project_root, task_id, commit, base, pipeline_sha)
    except GateError as error:
        raise LifecycleError(str(error)) from error
    if not report.passed:
        return CompletionResult(report, None)
    try:
        record = create_completed_record(task_id, __version__, report.resolved_commit)
        record_path = write_record(journal_root, task_id, record)
    except (JournalRecordError, OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    return CompletionResult(report, record_path)


def complete_findings_task(journal_root: Path, task_id: str) -> CompletionResult:
    """Gate the latest finding and bind completion to it on success."""

    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    if task.state != "open":
        raise LifecycleError(f"task {task_id} is not open (state: {task.state})")
    try:
        report = run_findings_gate(journal_root, task_id)
    except GateError as error:
        raise LifecycleError(str(error)) from error
    if not report.passed:
        return CompletionResult(report, None)
    assert report.resolved_finding is not None
    try:
        record = create_completed_record(
            task_id, __version__, None, completed_finding=report.resolved_finding
        )
        record_path = write_record(journal_root, task_id, record)
    except (JournalRecordError, OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    return CompletionResult(report, record_path)


def abandon_task(project_root: Path, task_id: str, reason: str) -> Path:
    """Record abandonment for an open task."""

    if not reason:
        raise LifecycleError("abandon reason must not be empty")
    journal_root = project_root / ".agentmarshal" / "journal"
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    if task.state != "open":
        raise LifecycleError(f"task {task_id} is not open (state: {task.state})")
    try:
        record = create_abandoned_record(task_id, __version__, reason)
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error
