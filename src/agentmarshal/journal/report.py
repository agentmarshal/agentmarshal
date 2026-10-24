"""Delegation economics projected from append-only journal records."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import MAX_PREC, Decimal, Inexact, localcontext
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

# The results that make a check record a refusal (ADR-0017 decision 3):
# `failed` and `error` both count; `passed` and `skipped` do not — the
# same two results `brief`'s last-failing-check section reads.
_FAILING_CHECK_RESULTS = frozenset({"failed", "error"})

# What a `Checks` line's number is (ADR-0017 decision 2): the report
# says it once, on the line after the count — the sentence the brief's
# last-failing-check section already prints.
_CHECK_DECLARATION = (
    "A check record is the observer's declaration of what the pipeline "
    "found on the commit, not proof of it."
)


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
class CostSum:
    """One currency's session-cost sums (ADR-0019 decision 4).

    ``reported`` and ``estimated`` never share a sum — the provenance of
    a figure stays with it — and nothing blends currencies: a sum in one
    currency is a figure the journal holds, a conversion would assert a
    rate it does not.
    """

    currency: str
    reported: Decimal | None = None
    estimated: Decimal | None = None


@dataclass(frozen=True)
class CostSums:
    """What the ``Cost`` lines of a scope print (ADR-0019 decision 4).

    ``costs`` are the per-currency sums sorted by currency code;
    ``sessions`` counts the sessions the sums admit — every measured
    session and every unmeasured one carrying a ``cost``;
    ``sessions_without_cost`` counts the measured sessions carrying no
    ``cost``; ``unmeasured`` counts every unmeasured session and
    ``unmeasured_without_cost`` those carrying no ``cost`` — the
    sessions the sums left out, the count a ``Cost`` line's
    ``unmeasured=<n>`` field carries.
    """

    costs: tuple[CostSum, ...]
    sessions: int
    sessions_without_cost: int
    unmeasured: int
    unmeasured_without_cost: int


@dataclass(frozen=True)
class TaskReport:
    """Measured work and terminal status for one task.

    ``unmeasured`` counts the task's unmeasured sessions — zero tokens
    and no ``usage`` block — the sessions the token sum left out. The
    cost sums admit every session but an unmeasured one carrying no
    ``cost``: a ``cost`` an unmeasured session recorded sums exactly as
    a measured session's does (ADR-0019 decision 4), ``sessions``
    counting the admitted sessions and ``sessions_without_cost`` the
    measured ones carrying no ``cost``. ``unmeasured_without_cost``
    counts the sessions the cost sums left out.
    """

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
    sessions: int = 0
    sessions_without_cost: int = 0
    costs: tuple[CostSum, ...] = ()
    unmeasured: int = 0
    unmeasured_without_cost: int = 0
    rejected_commits: int = 0


@dataclass(frozen=True)
class JournalReport:
    """Task-level measurements and their aggregate totals.

    The lead-time aggregate counts the ``done`` tasks whose every phase
    boundary carries a time (``lead_known``); ``lead_median`` and
    ``lead_maximum`` run over their ``completed`` minus ``opened`` spans
    alone, and ``lead_unknown`` counts the rest — counted, never
    averaged in (ADR-0019 decision 2). As on ``TaskReport``,
    ``unmeasured`` counts the journal's unmeasured sessions, the cost
    sums admit every session but an unmeasured one carrying no ``cost``,
    and ``unmeasured_without_cost`` counts the sessions those sums left
    out.
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
    sessions: int = 0
    sessions_without_cost: int = 0
    costs: tuple[CostSum, ...] = ()
    unmeasured: int = 0
    unmeasured_without_cost: int = 0
    rejected_commits: int = 0


@dataclass(frozen=True)
class FindingClassView:
    """One finding class: how often reviews recorded it, and examples.

    ``examples`` are up to three distinct finding ids of the class in
    the order the records give them (ADR-0016 decision 3).
    """

    name: str
    count: int
    examples: tuple[str, ...]


@dataclass(frozen=True)
class OpenDeferral:
    """One deferred advisory disposition still open (ADR-0016 decision 1).

    ``follow_up`` is the task the deferral names, ``None`` when it names
    none — both are open; ``follow_up_state`` is the follow-up's
    projected state or that the journal does not hold it.
    """

    task_id: str
    finding_id: str
    reason: str
    follow_up: str | None
    follow_up_state: str | None


@dataclass(frozen=True)
class FindingsReport:
    """The ``--findings`` view: classes across tasks and open deferrals."""

    classes: tuple[FindingClassView, ...]
    deferrals: tuple[OpenDeferral, ...]


def _is_unmeasured(record: dict[str, object]) -> bool:
    """Whether a session record measured nothing (digest 044's finding).

    ``record-session`` without token flags writes ``0/0/0`` — zeros
    indistinguishable from a free run, the only trace that nothing was
    measured being a missing ``usage`` block. Such a record reads as
    unmeasured: every token count zero and no ``usage`` block. A session
    carrying ``usage``, or any non-zero count, is measured — a recorded
    zero is a measurement. ``status`` and ``report`` share this one
    definition; making token counts optional on the write side waits for
    the next record schema.
    """

    tokens = record.get("tokens")
    return (
        record["record_type"] == "session"
        and "usage" not in record
        and isinstance(tokens, dict)
        and all(value == 0 for value in tokens.values())
    )


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


def _cost_sums(records: Iterable[dict[str, object]]) -> CostSums:
    """Sum session costs per currency and count sessions carrying none.

    A ``cost`` an unmeasured session — zero tokens and no ``usage``
    block — recorded sums exactly as a measured session's does: the sum
    holds the figure, and leaving it out would silently drop money the
    journal holds (ADR-0019 decision 4). Only an unmeasured session
    carrying no ``cost`` is left out of these sums — it is no measured
    session and no ``sessions_without_cost`` session — so
    ``unmeasured_without_cost`` carries what the lines would otherwise
    lose. The record holds ``amount`` as a string so a sum is exact —
    the sums are ``Decimal``, never floats — and ``reported`` and
    ``estimated`` keep separate sums: the provenance of a figure stays
    with it, and a conversion would assert a rate the journal does not
    hold (ADR-0019 decision 4).
    """

    reported: dict[str, Decimal] = {}
    estimated: dict[str, Decimal] = {}
    sessions = 0
    without_cost = 0
    unmeasured = 0
    unmeasured_without_cost = 0
    # An amount runs to more digits than the default context's 28; under
    # the maximum precision the addition of the recorded finite decimals
    # is exact, and a sum that still cannot be represented fails on the
    # Inexact trap rather than printing a rounded figure.
    with localcontext() as context:
        context.prec = MAX_PREC
        context.traps[Inexact] = True
        for record in records:
            if record["record_type"] != "session":
                continue
            cost = record.get("cost")
            if _is_unmeasured(record):
                unmeasured += 1
                if not isinstance(cost, dict):
                    unmeasured_without_cost += 1
                    continue
            sessions += 1
            if not isinstance(cost, dict):
                without_cost += 1
                continue
            amount = Decimal(str(cost["amount"]))
            currency = cast(str, cost["currency"])
            sums = reported if cost["source"] == "reported" else estimated
            sums[currency] = sums.get(currency, Decimal(0)) + amount
    return CostSums(
        costs=tuple(
            CostSum(currency, reported.get(currency), estimated.get(currency))
            for currency in sorted(reported.keys() | estimated.keys())
        ),
        sessions=sessions,
        sessions_without_cost=without_cost,
        unmeasured=unmeasured,
        unmeasured_without_cost=unmeasured_without_cost,
    )


def _rejected_commits(records: Iterable[dict[str, object]]) -> int:
    """The distinct commits a ``check`` record marked ``failed`` or ``error``.

    The candidates the pipeline rejected (ADR-0017 decision 3): the
    count is of commits, not records — two records on one commit are one
    rejected candidate.
    """

    return len(
        {
            record["commit"]
            for record in records
            if record["record_type"] == "check"
            and record.get("result") in _FAILING_CHECK_RESULTS
        }
    )


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
        if record["record_type"] == "session" and not _is_unmeasured(record)
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
    cost_sums = _cost_sums(records)
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
        sessions=cost_sums.sessions,
        sessions_without_cost=cost_sums.sessions_without_cost,
        costs=cost_sums.costs,
        unmeasured=cost_sums.unmeasured,
        unmeasured_without_cost=cost_sums.unmeasured_without_cost,
        rejected_commits=_rejected_commits(records),
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
    cost_sums = _cost_sums(record for status in statuses for record in status.records)
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
        sessions=cost_sums.sessions,
        sessions_without_cost=cost_sums.sessions_without_cost,
        costs=cost_sums.costs,
        unmeasured=cost_sums.unmeasured,
        unmeasured_without_cost=cost_sums.unmeasured_without_cost,
        rejected_commits=sum(task.rejected_commits for task in tasks),
    )


def _follow_up_state(journal_root: Path, follow_up: str) -> str:
    """The follow-up task's projected state, or that it is not held.

    ``load_task_status`` raises for a task the journal does not hold —
    the ordinary answer here, not an error; ``status``'s deferral
    section reads the same failure the same way.
    """

    try:
        state = load_task_status(journal_root, follow_up).state
    except (OSError, TaskStatusError, ValueError):
        return "not held by the journal"
    return f"state: {state}"


def build_findings_report(
    journal_root: Path, task_id: str | None = None
) -> FindingsReport:
    """Read journal evidence and project finding classes and open deferrals.

    A deferral — a ``deferred`` entry of a ``completed`` record's
    ``advisory_dispositions`` — is open while its ``follow_up`` names no
    task or a task the journal does not hold as completed (ADR-0016
    decision 1); a follow-up held as ``done`` closes it.
    """

    try:
        # ``--task`` scopes the view to the one task's records, the same
        # scoping ``build_report`` makes.
        if task_id is not None:
            statuses = [load_task_status(journal_root, task_id)]
        else:
            statuses = list_task_statuses(journal_root)
        counts: dict[str, int] = {}
        examples: dict[str, list[str]] = {}
        deferrals: list[OpenDeferral] = []
        follow_up_states: dict[str, str] = {}
        for status in statuses:
            for record in status.records:
                record_type = record["record_type"]
                if record_type == "review":
                    classes = record.get("classes")
                    if not isinstance(classes, dict):
                        continue
                    for finding_id, name in classes.items():
                        if not isinstance(name, str):
                            continue
                        counts[name] = counts.get(name, 0) + 1
                        ids = examples.setdefault(name, [])
                        shown = str(finding_id)
                        if len(ids) < 3 and shown not in ids:
                            ids.append(shown)
                elif record_type == "completed":
                    dispositions = record.get("advisory_dispositions")
                    if not isinstance(dispositions, dict):
                        continue
                    for finding_id, entry in dispositions.items():
                        if (
                            not isinstance(entry, dict)
                            or entry.get("disposition") != "deferred"
                        ):
                            continue
                        follow_up = entry.get("follow_up")
                        state = None
                        if isinstance(follow_up, str) and follow_up:
                            if follow_up not in follow_up_states:
                                follow_up_states[follow_up] = _follow_up_state(
                                    journal_root, follow_up
                                )
                            state = follow_up_states[follow_up]
                            if state == "state: done":
                                continue
                        reason = entry.get("reason")
                        deferrals.append(
                            OpenDeferral(
                                status.task_id,
                                str(finding_id),
                                reason
                                if isinstance(reason, str) and reason
                                else "(absent)",
                                follow_up if isinstance(follow_up, str) else None,
                                state,
                            )
                        )
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReportError(str(error)) from error
    return FindingsReport(
        tuple(
            FindingClassView(name, counts[name], tuple(examples[name]))
            for name in sorted(counts)
        ),
        tuple(deferrals),
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


def _cost_lines(sums: CostSums) -> list[str]:
    """The ``Cost`` lines: one per currency, then the no-cost count.

    A currency's ``reported`` and ``estimated`` sums print as decimals
    in plain notation — the record's own spelling (``f`` keeps a small
    sum ``0.000000001`` rather than ``1E-9``) — and the count prints
    whenever the scope holds a session the sums admit, so "no cost"
    reads as a count rather than a zero sum (ADR-0019 decision 4). Every
    line the block prints carries ``unmeasured=<n>`` as its last field
    whenever the scope left sessions out of these sums as unmeasured —
    the count says what the sums would otherwise silently lose.
    """

    unmeasured_field = (
        f"\tunmeasured={sums.unmeasured_without_cost}"
        if sums.unmeasured_without_cost
        else ""
    )
    lines = []
    for cost in sums.costs:
        line = f"Cost\t{escape_for_display(cost.currency)}"
        if cost.reported is not None:
            line += f"\treported={cost.reported:f}"
        if cost.estimated is not None:
            line += f"\testimated={cost.estimated:f}"
        lines.append(line + unmeasured_field)
    if sums.sessions:
        lines.append(
            f"Cost\tsessions_without_cost={sums.sessions_without_cost}"
            f"{unmeasured_field}"
        )
    return lines


def _check_lines(rejected_commits: int) -> list[str]:
    """The ``Checks`` line and the declaration the report says once."""

    return [f"Checks\trejected_commits={rejected_commits}", _CHECK_DECLARATION]


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
        if task.unmeasured:
            line += f"\tunmeasured={task.unmeasured}"
        lines.append(line)
        if not include_summary:
            lines.extend(_phase_lines(task))
            lines.extend(
                _cost_lines(
                    CostSums(
                        costs=task.costs,
                        sessions=task.sessions,
                        sessions_without_cost=task.sessions_without_cost,
                        unmeasured=task.unmeasured,
                        unmeasured_without_cost=task.unmeasured_without_cost,
                    )
                )
            )
            lines.extend(_check_lines(task.rejected_commits))
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
    if report.unmeasured:
        summary += f"\tunmeasured={report.unmeasured}"
    lines.append(summary)
    lead = f"Lead\tknown={report.lead_known}"
    if report.lead_median is not None:
        lead += f"\tmedian={_duration(report.lead_median)}"
    if report.lead_maximum is not None:
        lead += f"\tmax={_duration(report.lead_maximum)}"
    lines.append(f"{lead}\tunknown={report.lead_unknown}")
    lines.extend(
        _cost_lines(
            CostSums(
                costs=report.costs,
                sessions=report.sessions,
                sessions_without_cost=report.sessions_without_cost,
                unmeasured=report.unmeasured,
                unmeasured_without_cost=report.unmeasured_without_cost,
            )
        )
    )
    lines.extend(_check_lines(report.rejected_commits))
    return tuple(lines)


def format_findings_report(report: FindingsReport) -> tuple[str, ...]:
    """Return the ``--findings`` view's lines for CLI output.

    Every value taken from a record — a class name, a finding or task
    id, a reason, a follow-up — is escaped where it is interpolated, as
    on the report's other lines (ADR-0015 decision 5).
    """

    lines = []
    if not report.classes:
        lines.append("Classes\t(none)")
    for entry in report.classes:
        lines.append(
            f"Classes\t{escape_for_display(entry.name)}\tcount={entry.count}"
            "\texamples="
            + ",".join(escape_for_display(finding) for finding in entry.examples)
        )
    if not report.deferrals:
        lines.append("Deferrals\t(none)")
    for deferral in report.deferrals:
        follow_up = (
            "(none)"
            if deferral.follow_up is None
            else escape_for_display(deferral.follow_up)
            + f" ({deferral.follow_up_state})"
        )
        lines.append(
            f"Deferrals\ttask={escape_for_display(deferral.task_id)}"
            f"\tfinding={escape_for_display(deferral.finding_id)}"
            f"\treason={escape_for_display(deferral.reason)}"
            f"\tfollow_up={follow_up}"
        )
    return tuple(lines)
