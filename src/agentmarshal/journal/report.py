"""Delegation economics projected from append-only journal records."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.records import JournalRecordError, _utc_timestamp
from agentmarshal.journal.status import (
    TaskStatus,
    TaskStatusError,
    list_task_statuses,
    load_task_status,
)


class ReportError(Exception):
    """Raised when journal measurements cannot be safely reported."""


# The lead-time markers of ADR-0019 decision 2: ``unknown`` where a
# record exists but cannot supply the boundary's time — a session
# written before ``started_at`` existed — and ``not yet`` where the
# event has no record at all. A session's ``created_at`` is its write
# time, never a stand-in.
_UNKNOWN = "unknown"
_NOT_YET = "not yet"

# The lead-time chain in order (ADR-0019 decision 2): opened, the first
# implementer session's start, the first review, approval, completion.
_PHASES = ("opened", "implementer", "review", "approval", "completed")


@dataclass(frozen=True)
class PhaseBoundary:
    """One lead-time boundary: what it prints, and its instant if known.

    ``shown`` is the record's timestamp text or a marker — ``unknown``
    or ``not yet``; ``at`` is the parsed instant, ``None`` on a marker.
    """

    shown: str
    at: datetime | None = None


@dataclass(frozen=True)
class ReviewRound:
    """One review round: its verdict and the time since the previous one.

    ``since`` is measured from the first implementer session's start for
    the first round — ``None`` where that boundary cannot supply a time.
    """

    verdict: str
    since: timedelta | None


@dataclass(frozen=True)
class TaskReport:
    """Measured work and terminal status for one task."""

    task_id: str
    state: str
    review_cycles: int
    tokens: int
    artifacts: int = 0
    usage_provenance: str | None = None
    decision: str | None = None
    phases: tuple[PhaseBoundary, ...] = ()
    rounds: tuple[ReviewRound, ...] = ()
    lead_time: timedelta | None = None


@dataclass(frozen=True)
class JournalReport:
    """Task-level measurements and their aggregate totals.

    The lead-time aggregate counts the ``done`` tasks whose every phase
    boundary carries a time (``lead_known``); ``lead_median`` and
    ``lead_maximum`` run over their ``completed`` minus ``opened`` spans
    alone, and ``lead_unknown`` counts the rest — counted, never
    averaged in (ADR-0019 decision 2).
    """

    tasks: tuple[TaskReport, ...]
    review_cycles: int
    tokens: int
    artifacts: int = 0
    usage_provenance: str | None = None
    lead_known: int = 0
    lead_median: timedelta | None = None
    lead_maximum: timedelta | None = None
    lead_unknown: int = 0


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


def _record_boundary(record: dict[str, object] | None) -> PhaseBoundary:
    """The boundary a lifecycle record supplies, or ``not yet`` without it.

    ``created_at`` is the record's write time — for the lifecycle records
    written as their event happens, it is the event's time.
    """

    if record is None:
        return PhaseBoundary(_NOT_YET)
    shown = cast(str, record["created_at"])
    return PhaseBoundary(shown, _utc_timestamp(shown, "record field 'created_at'"))


def _implementer_boundary(records: tuple[dict[str, object], ...]) -> PhaseBoundary:
    """The first implementer session's start, or the marker saying why not.

    An implementer session is a session record whose ``role`` is
    ``implementer`` — the sense ``status`` already gives the word. Where
    the first lacks ``started_at`` the boundary is ``unknown``: the
    record's ``created_at`` is its write time, never its start
    (ADR-0019 decision 2), and a later session's ``started_at`` is a
    different, later boundary.
    """

    session = next(
        (
            record
            for record in records
            if record["record_type"] == "session"
            and record.get("role") == "implementer"
        ),
        None,
    )
    if session is None:
        return PhaseBoundary(_NOT_YET)
    started_at = session.get("started_at")
    if not isinstance(started_at, str):
        return PhaseBoundary(_UNKNOWN)
    return PhaseBoundary(
        started_at, _utc_timestamp(started_at, "session record field 'started_at'")
    )


def _phases(records: tuple[dict[str, object], ...]) -> tuple[PhaseBoundary, ...]:
    reviews = [record for record in records if record["record_type"] == "review"]
    completed = [record for record in records if record["record_type"] == "completed"]
    return (
        _record_boundary(
            next(
                (record for record in records if record["record_type"] == "opened"),
                None,
            )
        ),
        _implementer_boundary(records),
        _record_boundary(reviews[0] if reviews else None),
        _record_boundary(
            next(
                (record for record in reviews if record.get("verdict") == "approved"),
                None,
            )
        ),
        _record_boundary(completed[-1] if completed else None),
    )


def _rounds(
    records: tuple[dict[str, object], ...], implementer: PhaseBoundary
) -> tuple[ReviewRound, ...]:
    """The task's review rounds in order, each timed since the previous one."""

    rounds = []
    previous_at = implementer.at
    for record in records:
        if record["record_type"] != "review":
            continue
        at = _utc_timestamp(
            cast(str, record["created_at"]), "record field 'created_at'"
        )
        rounds.append(
            ReviewRound(
                cast(str, record["verdict"]),
                None if previous_at is None else at - previous_at,
            )
        )
        previous_at = at
    return tuple(rounds)


def _lead_time(state: str, phases: tuple[PhaseBoundary, ...]) -> timedelta | None:
    """The task's lead time when it is completed and fully known, else ``None``.

    The lead time is ``completed`` minus ``opened``; "fully known" is the
    stronger claim the aggregate makes — every boundary of the chain
    carries a time, so the report accounts for the whole span, not just
    its ends (ADR-0019 decision 2).
    """

    if state != "done" or any(boundary.at is None for boundary in phases):
        return None
    return cast(datetime, phases[-1].at) - cast(datetime, phases[0].at)


def _task_report(status: TaskStatus) -> TaskReport:
    records = status.records
    review_cycles = sum(record["record_type"] == "review" for record in records)
    artifacts = sum(
        len(cast(list[object], record.get("artifacts", [])))
        for record in records
        if record["record_type"] == "review"
    )
    tokens = sum(
        sum(cast(dict[str, int], record["tokens"]).values())
        for record in records
        if record["record_type"] == "session"
    )
    decision = None
    if any(
        record["record_type"] == "acceptance" and "findings" in record
        for record in records
    ):
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
    phases = _phases(records)
    return TaskReport(
        status.task_id,
        status.state,
        review_cycles,
        tokens,
        artifacts=artifacts,
        usage_provenance=_usage_provenance(records),
        decision=decision,
        phases=phases,
        rounds=_rounds(records, phases[1]),
        lead_time=_lead_time(status.state, phases),
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
    lead_times = sorted(
        task.lead_time
        for task in tasks
        if task.state == "done" and task.lead_time is not None
    )
    lead_median = None
    if lead_times:
        middle = len(lead_times) // 2
        lead_median = (
            lead_times[middle]
            if len(lead_times) % 2
            else (lead_times[middle - 1] + lead_times[middle]) / 2
        )
    return JournalReport(
        tasks,
        sum(task.review_cycles for task in tasks),
        sum(task.tokens for task in tasks),
        artifacts=sum(task.artifacts for task in tasks),
        usage_provenance=_usage_provenance(
            [record for status in statuses for record in status.records]
        ),
        lead_known=len(lead_times),
        lead_median=lead_median,
        lead_maximum=max(lead_times) if lead_times else None,
        lead_unknown=sum(
            task.state == "done" and task.lead_time is None for task in tasks
        ),
    )


def _duration(span: timedelta) -> str:
    """Render an elapsed span in the ``--deadline`` duration spelling.

    ``90m``, ``1h30m`` and ``1d3h4m7s`` are the units a ``step``
    deadline is given and an overdue span printed in, spelled out here
    rather than imported — the journal package does not read the
    process-log machinery the step commands live beside (ADR-0014).
    A negative span keeps its sign rather than clamping to ``0s``: the
    confidently wrong number is the failure ADR-0019 decision 2 rules
    out.
    """

    negative = span < timedelta(0)
    seconds = int(abs(span).total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    rendered = "".join(
        f"{amount}{unit}"
        for amount, unit in (
            (days, "d"),
            (hours, "h"),
            (minutes, "m"),
            (seconds, "s"),
        )
        if amount
    )
    if not rendered:
        return "0s"
    return ("-" if negative else "") + rendered


def _span(left: PhaseBoundary, right: PhaseBoundary) -> str:
    """The elapsed time between two boundaries, or the marker saying why not.

    ``not yet`` while the later event has no record — the span is still
    open; ``unknown`` when it is over but a boundary cannot say.
    """

    if right.shown == _NOT_YET:
        return _NOT_YET
    if left.at is None or right.at is None:
        return _UNKNOWN
    return _duration(right.at - left.at)


def _phase_lines(task: TaskReport) -> list[str]:
    """The ``--task`` view's phase, duration and round lines.

    Each boundary prints the record's timestamp or the marker the record
    cannot avoid — ``unknown`` or ``not yet`` — and the values are
    escaped where they are interpolated, as on the task line.
    """

    boundaries = task.phases
    lines = []
    if len(boundaries) == len(_PHASES):
        lines = [
            "Phases"
            + "".join(
                f"\t{name}={escape_for_display(boundary.shown)}"
                for name, boundary in zip(_PHASES, boundaries, strict=True)
            ),
            "Durations"
            + "".join(
                f"\t{_PHASES[index]}->{_PHASES[index + 1]}="
                f"{_span(boundaries[index], boundaries[index + 1])}"
                for index in range(len(boundaries) - 1)
            ),
        ]
    for index, round_ in enumerate(task.rounds, start=1):
        since = _UNKNOWN if round_.since is None else _duration(round_.since)
        lines.append(
            f"Round\t{index}\tverdict={escape_for_display(round_.verdict)}"
            f"\tsince={since}"
        )
    return lines


def format_report(
    report: JournalReport, *, include_summary: bool = True
) -> tuple[str, ...]:
    """Return stable, tab-separated report lines for CLI output."""

    # Each value taken from a record or a contract is escaped where it is
    # interpolated — the tabs are structure and must survive (ADR-0015
    # decision 5). ``state`` and ``decision`` are labels the tool derives
    # from closed sets — its own text — and print as they are.
    lines = []
    for task in report.tasks:
        line = (
            f"{escape_for_display(task.task_id)}\t{task.state}"
            f"\treviews={task.review_cycles}\ttokens={task.tokens}"
        )
        if task.artifacts:
            line += f"\tartifacts={task.artifacts}"
        if task.usage_provenance is not None:
            line += f"\tusage={escape_for_display(task.usage_provenance)}"
        if task.decision is not None:
            line += f"\tdecision={task.decision}"
        lines.append(line)
        if not include_summary:
            lines.extend(_phase_lines(task))
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
    if report.artifacts:
        summary += f"\tartifacts={report.artifacts}"
    if report.usage_provenance is not None:
        summary += f"\tusage={escape_for_display(report.usage_provenance)}"
    lines.append(summary)
    lead = f"Lead\tknown={report.lead_known}"
    if report.lead_median is not None:
        lead += f"\tmedian={_duration(report.lead_median)}"
    if report.lead_maximum is not None:
        lead += f"\tmax={_duration(report.lead_maximum)}"
    lines.append(f"{lead}\tunknown={report.lead_unknown}")
    return tuple(lines)
