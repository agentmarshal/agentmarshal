"""Trusted recording path for attributed task work sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from agentmarshal import __version__
from agentmarshal.journal.records import (
    _COST_AMOUNT_PATTERN,
    _COST_CURRENCY_PATTERN,
    _PROVIDER_LIMIT_OUTCOME,
    JournalRecordError,
    _utc_timestamp,
    create_session_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record


class SessionRecordError(Exception):
    """Raised when a work session cannot be recorded."""


@dataclass(frozen=True)
class RecordedSession:
    """What ``record_session`` leaves behind, in one of its two shapes.

    ``record_path`` is the path of the record just written. ``existing_id``
    is the id of the session record an ``if_missing`` repeat matched — the
    write is then a no-op and no path exists to report. Exactly one is set.
    """

    record_path: Path | None = None
    existing_id: str | None = None


def _session_flags_refusal(
    outcome: str,
    *,
    started_at: str | None,
    ended_at: str | None,
    resets_at: str | None,
    cost_amount: str | None,
    cost_currency: str | None,
    cost_source: str | None,
) -> str | None:
    """The refusal the session's time, reset and cost flags earn, or None.

    Restates the ``session-fields-7`` rule with flag names — what the
    operator typed was a flag, so a refusal names it, the
    ``reviewer_actor_refusal`` pattern — and lands before anything is
    written rather than after the record rule's field-named one. Where the
    rule has a predicate the flag layer calls it: ``_utc_timestamp`` for
    the three timestamps, passed the flag name as its ``what`` so the
    refusal is the rule's own wording, and the two cost patterns, so the
    checks cannot drift on what a timestamp or a decimal is.
    ``--cost-source`` carries ``choices`` and argparse names the flag on a
    word outside the vocabulary before this ever runs.
    """

    if (started_at is None) != (ended_at is None):
        missing = "--ended-at" if ended_at is None else "--started-at"
        supplied = "--started-at" if ended_at is None else "--ended-at"
        return f"{missing} is required when {supplied} is supplied"
    timestamps: dict[str, datetime] = {}
    for flag, value in (
        ("--started-at", started_at),
        ("--ended-at", ended_at),
        ("--resets-at", resets_at),
    ):
        if value is None:
            continue
        try:
            timestamps[flag] = _utc_timestamp(value, flag)
        except JournalRecordError as error:
            return str(error)
    if started_at is not None and (
        timestamps["--ended-at"] < timestamps["--started-at"]
    ):
        return "--ended-at must not be earlier than --started-at"
    if resets_at is not None and outcome != _PROVIDER_LIMIT_OUTCOME:
        return f"--resets-at is admitted on a '{_PROVIDER_LIMIT_OUTCOME}' outcome alone"
    supplied_cost = (
        cost_amount is not None,
        cost_currency is not None,
        cost_source is not None,
    )
    if any(supplied_cost) and not all(supplied_cost):
        return (
            "--cost-amount, --cost-currency and --cost-source must be supplied together"
        )
    if cost_amount is not None and _COST_AMOUNT_PATTERN.fullmatch(cost_amount) is None:
        return (
            "--cost-amount must be a non-negative decimal written as a "
            "string of digits with an optional fractional part"
        )
    if (
        cost_currency is not None
        and _COST_CURRENCY_PATTERN.fullmatch(cost_currency) is None
    ):
        return "--cost-currency must be exactly three uppercase ASCII letters"
    return None


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
    commit: str | None = None,
    model: str | None = None,
    trace: str | None = None,
    cli_session: str | None = None,
    report_ready: bool | None = None,
    fallback_reason: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
    resets_at: str | None = None,
    cost_amount: str | None = None,
    cost_currency: str | None = None,
    cost_source: str | None = None,
    if_missing: bool = False,
) -> RecordedSession:
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

    ``started_at`` with ``ended_at``, ``resets_at`` and the cost triple are
    the time, reset and cost fields of ADR-0019 decisions 1, 3 and 4 — the
    remaining fields of the schema-7 session family. Their refusals are
    restated with flag names before anything is read or written; the record
    rules stay the only judge of a value that passes. ``if_missing`` is
    decision 6: a write under a ``task + role + actor + activity`` the task
    already holds a session for is a no-op returning the existing record's
    id, so cost recording after completion is safe to repeat.
    """

    refusal = _session_flags_refusal(
        outcome,
        started_at=started_at,
        ended_at=ended_at,
        resets_at=resets_at,
        cost_amount=cost_amount,
        cost_currency=cost_currency,
        cost_source=cost_source,
    )
    if refusal is not None:
        raise SessionRecordError(refusal)
    try:
        task = load_task_for_record(journal_root, task_id, "session")
        if if_missing:
            for record in task.records:
                if (
                    record.get("record_type") == "session"
                    and record.get("role") == role
                    and record.get("actor") == actor
                    and record.get("activity") == activity
                ):
                    return RecordedSession(existing_id=cast(str, record["id"]))
        cost = None
        if (
            cost_amount is not None
            and cost_currency is not None
            and cost_source is not None
        ):
            cost = {
                "amount": cost_amount,
                "currency": cost_currency,
                "source": cost_source,
            }
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
            commit=commit,
            model=model,
            trace=trace,
            cli_session=cli_session,
            report_ready=report_ready,
            fallback_reason=fallback_reason,
            started_at=started_at,
            ended_at=ended_at,
            resets_at=resets_at,
            cost=cost,
        )
        return RecordedSession(record_path=write_record(journal_root, task_id, record))
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise SessionRecordError(str(error)) from error
