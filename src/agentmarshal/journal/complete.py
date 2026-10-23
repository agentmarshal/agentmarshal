"""Terminal lifecycle transactions: completion and abandonment.

Completion is automated on a passing merge: ``complete`` runs the gate
itself and records completion only when the gate passes (founding brief;
ADR-0004 keeps state a projection, so completion is an append-only
record, not a directory move).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.display import escape_for_display
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
    read_records,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record


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
    *,
    dispositions: Iterable[str] = (),
    follow_ups: Iterable[str] = (),
) -> CompletionResult:
    """Gate the candidate and record completion only when the gate passes."""

    journal_root = project_root / ".agentmarshal" / "journal"
    try:
        load_task_for_record(journal_root, task_id, "completed")
    except (OSError, TaskStatusError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    try:
        report = run_gate(project_root, task_id, commit, base, pipeline_sha)
    except GateError as error:
        raise LifecycleError(str(error)) from error
    if not report.passed:
        return CompletionResult(report, None)
    record_path = record_commit_completion(
        journal_root,
        task_id,
        report.resolved_commit,
        dispositions=dispositions,
        follow_ups=follow_ups,
    )
    return CompletionResult(report, record_path)


def record_commit_completion(
    journal_root: Path,
    task_id: str,
    resolved_commit: str,
    *,
    dispositions: Iterable[str] = (),
    follow_ups: Iterable[str] = (),
) -> Path:
    """Write the ``completed`` record a passed gate earned for a commit.

    The review the gate passed on — the latest review of the resolved
    commit, the approving one or the non-approving one an acceptance
    covered, the same one the gate's verdict check consults (gate.py) —
    decides the dispositions the record must carry (ADR-0016 decision
    1): each of its advisory findings takes a repeatable
    ``--disposition <id>=fixed``, ``--disposition <id>=deferred:<reason>``
    or ``--disposition <id>=rejected:<reason>`` — the reason is
    everything after the first colon — and a deferred one may name a
    follow-up task through ``--follow-up <id>=<task>``. Every refusal —
    a malformed flag, an id that is no advisory finding of that review,
    an advisory finding left unanswered, a value the record rules
    refuse — precedes the write and names the flag or the ids at fault.
    """

    entries, tasks = _parse_disposition_arguments(dispositions, follow_ups)
    advisory_ids = _advisory_ids_of_the_review_the_gate_passed_on(
        journal_root, task_id, resolved_commit
    )
    answered = list(dict.fromkeys([*entries, *tasks]))
    unknown = [finding_id for finding_id in answered if finding_id not in advisory_ids]
    if unknown:
        raise LifecycleError(
            "not an advisory finding of the review the gate passed on: "
            + ", ".join(escape_for_display(finding_id) for finding_id in unknown)
        )
    missing = [finding_id for finding_id in advisory_ids if finding_id not in entries]
    if missing:
        raise LifecycleError(
            "each advisory finding of the review the gate passed on takes a "
            "--disposition; missing: "
            + ", ".join(escape_for_display(finding_id) for finding_id in missing)
        )
    for finding_id, task in tasks.items():
        entries[finding_id]["follow_up"] = task
    field = entries or None
    try:
        record = create_completed_record(
            task_id, __version__, resolved_commit, advisory_dispositions=field
        )
        return write_record(journal_root, task_id, record)
    except JournalRecordError as error:
        if field is None:
            raise LifecycleError(str(error)) from error
        # What the operator typed were flags: a refusal the record rules
        # raise against the field is repeated naming the flag it came
        # through — the record's message already names the finding id
        # and the key at fault.
        flag = "--follow-up" if "'follow_up'" in str(error) else "--disposition"
        raise LifecycleError(f"{flag}: {error}") from error
    except (OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error


def _parse_disposition_arguments(
    dispositions: Iterable[str], follow_ups: Iterable[str]
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """Parse the repeatable flags into disposition entries and follow-ups.

    ``<id>=<disposition>[:<reason>]`` — the reason is everything after
    the first colon, so it may contain colons — and ``<id>=<task>``. A
    value with no ``=`` or an empty id, a duplicated id and a follow-up
    with an empty task are refused naming the flag; every other shape
    refusal is the record rules', repeated flag-named at the write.
    """

    entries: dict[str, dict[str, str]] = {}
    for argument in dispositions:
        finding_id, separator, value = argument.partition("=")
        if not separator or not finding_id:
            raise LifecycleError(
                "--disposition expects <finding id>=<disposition>[:<reason>], "
                f"got '{escape_for_display(argument)}'"
            )
        if finding_id in entries:
            raise LifecycleError(
                f"--disposition given twice for {escape_for_display(finding_id)}"
            )
        word, colon, reason = value.partition(":")
        entry = {"disposition": word}
        if colon:
            entry["reason"] = reason
        entries[finding_id] = entry
    tasks: dict[str, str] = {}
    for argument in follow_ups:
        finding_id, separator, task = argument.partition("=")
        if not separator or not finding_id or not task:
            raise LifecycleError(
                "--follow-up expects <finding id>=<task id>, "
                f"got '{escape_for_display(argument)}'"
            )
        if finding_id in tasks:
            raise LifecycleError(
                f"--follow-up given twice for {escape_for_display(finding_id)}"
            )
        tasks[finding_id] = task
    return entries, tasks


def _advisory_ids_of_the_review_the_gate_passed_on(
    journal_root: Path, task_id: str, resolved_commit: str
) -> list[str]:
    """The advisory finding ids of the review the gate passed on.

    That review is the latest review of the resolved commit — the
    approving one or the non-approving one an acceptance covered, the
    same ``reviews[-1]`` the gate's verdict check consults (gate.py).
    """

    try:
        records = read_records(journal_root, task_id)
    except (JournalRecordError, OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    reviews = [
        record
        for record in records
        if record.get("record_type") == "review"
        and record.get("reviewed_commit") == resolved_commit
    ]
    if not reviews:
        return []
    advisory = reviews[-1].get("advisory_findings")
    if not isinstance(advisory, list):
        return []
    return [finding_id for finding_id in advisory if isinstance(finding_id, str)]


def complete_findings_task(journal_root: Path, task_id: str) -> CompletionResult:
    """Gate the latest finding and bind completion to it on success."""

    try:
        load_task_for_record(journal_root, task_id, "completed")
    except (OSError, TaskStatusError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    try:
        report = run_findings_gate(journal_root, task_id)
    except GateError as error:
        raise LifecycleError(str(error)) from error
    if not report.passed:
        return CompletionResult(report, None)
    if report.resolved_finding is None:
        raise LifecycleError(
            f"findings gate passed for {task_id} without resolving a finding"
        )
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
        load_task_for_record(journal_root, task_id, "abandoned")
    except (OSError, TaskStatusError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    try:
        record = create_abandoned_record(task_id, __version__, reason)
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error
