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
    validate_record_for_write,
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
        resolved_review=report.resolved_review,
        dispositions=dispositions,
        follow_ups=follow_ups,
    )
    return CompletionResult(report, record_path)


def record_commit_completion(
    journal_root: Path,
    task_id: str,
    resolved_commit: str,
    *,
    resolved_review: str | None = None,
    dispositions: Iterable[str] = (),
    follow_ups: Iterable[str] = (),
) -> Path:
    """Write the ``completed`` record a passed gate earned for a commit.

    The review the gate passed on — the approving latest review of the
    resolved commit, or the non-approving one an acceptance covered —
    decides the dispositions the record must carry (ADR-0016 decision
    1). A caller holding the gate's report passes its
    ``resolved_review``: the id the verdict check itself set, so the
    advisory findings owed are read from the record of the review
    actually judged, and a review appended after the gate ran names a
    different id and cannot change which are owed. A caller that cannot
    name it — the sidecar's ``complete``, whose call predates the field
    — derives the review as the verdict check does: the latest review
    of the resolved commit. Each of that review's advisory findings
    takes a repeatable ``--disposition <id>=fixed``,
    ``--disposition <id>=deferred:<reason>`` or
    ``--disposition <id>=rejected:<reason>`` — the reason is
    everything after the first colon — and a deferred one may name a
    follow-up task through ``--follow-up <id>=<task>``. Every refusal —
    a malformed flag, an id that is no advisory finding of that review,
    an advisory finding left unanswered, a value the record rules
    refuse — precedes the write and names the flag or the ids at fault.
    """

    advisory_ids = _advisory_ids_of_the_review_the_gate_passed_on(
        journal_root, task_id, resolved_commit, resolved_review
    )
    disposition_arguments = _split_flag_arguments(
        "--disposition", dispositions, advisory_ids
    )
    follow_up_arguments = _split_flag_arguments("--follow-up", follow_ups, advisory_ids)
    answered = {argument.finding_id for argument in disposition_arguments}
    missing = [finding_id for finding_id in advisory_ids if finding_id not in answered]
    if missing:
        raise LifecycleError(
            "each advisory finding of the review the gate passed on takes a "
            "--disposition; missing: "
            + ", ".join(escape_for_display(finding_id) for finding_id in missing)
        )
    # The field is built piece by piece and the record rules run after
    # every addition: a refusal lands exactly when the piece at fault is
    # added, so it is repeated naming the flag that piece came through —
    # carried on the argument, never read off the refusal's text.
    field: dict[str, dict[str, str]] = {}
    for argument in (*disposition_arguments, *follow_up_arguments):
        entry = field.setdefault(argument.finding_id, {})
        if argument.flag == "--disposition":
            # The reason is everything after the first colon, so it may
            # contain colons.
            word, colon, reason = argument.value.partition(":")
            entry["disposition"] = word
            if colon:
                entry["reason"] = reason
        else:
            entry["follow_up"] = argument.value
        _run_record_rules_over(
            field, journal_root, task_id, resolved_commit, argument.flag
        )
    dispositions_field = field or None
    try:
        record = create_completed_record(
            task_id,
            __version__,
            resolved_commit,
            advisory_dispositions=dispositions_field,
        )
        return write_record(journal_root, task_id, record)
    except JournalRecordError as error:
        raise LifecycleError(str(error)) from error
    except (OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error


@dataclass(frozen=True)
class _FlagArgument:
    """One parsed ``--disposition``/``--follow-up`` value.

    The flag it came through rides along so every refusal names it —
    the flag is carried data, never inferred from a refusal's text (an
    advisory finding may legitimately be named ``follow_up``).
    """

    flag: str
    finding_id: str
    value: str


def _split_flag_arguments(
    flag: str, arguments: Iterable[str], advisory_ids: list[str]
) -> list[_FlagArgument]:
    """Split each flag value against the advisory ids it can name.

    Each value is ``<finding id>=<rest>`` where the finding id is the
    LONGEST of the review's advisory ids the value starts with followed
    by ``=`` — an advisory id may itself carry ``=``, so splitting on
    the first ``=`` would misread it. A value that starts with no known
    id followed by ``=`` — an unknown id, a bare id, no ``=`` at all —
    is refused naming the flag and listing the review's advisory ids,
    as is an id one flag names twice.
    """

    parsed: list[_FlagArgument] = []
    seen: set[str] = set()
    for argument in arguments:
        finding_id = _longest_advisory_id_prefix(argument, advisory_ids)
        if finding_id is None:
            raise LifecycleError(
                f"{flag} value '{escape_for_display(argument)}' names no "
                "advisory finding of the review the gate passed on; its "
                "advisory findings: "
                + (
                    ", ".join(
                        escape_for_display(finding_id) for finding_id in advisory_ids
                    )
                    or "none"
                )
            )
        if finding_id in seen:
            raise LifecycleError(
                f"{flag} given twice for {escape_for_display(finding_id)}"
            )
        seen.add(finding_id)
        parsed.append(_FlagArgument(flag, finding_id, argument[len(finding_id) + 1 :]))
    return parsed


def _longest_advisory_id_prefix(argument: str, advisory_ids: list[str]) -> str | None:
    """The longest advisory id `argument` starts with followed by ``=``."""

    match: str | None = None
    for finding_id in advisory_ids:
        if argument.startswith(finding_id + "=") and (
            match is None or len(finding_id) > len(match)
        ):
            match = finding_id
    return match


def _run_record_rules_over(
    field: dict[str, dict[str, str]],
    journal_root: Path,
    task_id: str,
    resolved_commit: str,
    flag: str,
) -> None:
    """Run the record's own write-time rules on `field` as it stands.

    Called after each parsed piece lands — `create_completed_record`
    only builds, the rules run in `validate_record_for_write`: a
    refusal fires exactly when the piece at fault was added, so the
    repeated refusal names the flag that piece came through, and the
    record's message already names the finding id and the key at fault.
    """

    try:
        record = create_completed_record(
            task_id,
            __version__,
            resolved_commit,
            advisory_dispositions=dict(field),
        )
        validate_record_for_write(journal_root, task_id, record)
    except JournalRecordError as error:
        raise LifecycleError(f"{flag}: {error}") from error


def _advisory_ids_of_the_review_the_gate_passed_on(
    journal_root: Path,
    task_id: str,
    resolved_commit: str,
    resolved_review: str | None,
) -> list[str]:
    """The advisory finding ids of the review the gate passed on.

    With ``resolved_review`` — the id the gate's verdict check set into
    its report — the review is the record carrying that id among the
    records the gate evaluated: a review appended after the gate ran
    carries a different id and cannot change which advisory findings
    are owed. Without it — a caller predating the field — the review is
    derived as the verdict check derives it: the latest review of the
    resolved commit (``reviews[-1]``, gate.py).
    """

    try:
        records = read_records(journal_root, task_id)
    except (JournalRecordError, OSError, ValueError) as error:
        raise LifecycleError(str(error)) from error
    if resolved_review is None:
        reviews = [
            record
            for record in records
            if record.get("record_type") == "review"
            and record.get("reviewed_commit") == resolved_commit
        ]
        review = reviews[-1] if reviews else None
    else:
        review = next(
            (
                record
                for record in records
                if record.get("record_type") == "review"
                and record.get("id") == resolved_review
            ),
            None,
        )
        if review is None:
            raise LifecycleError(
                "the review the gate passed on is not among the task's "
                f"records: {escape_for_display(resolved_review)}"
            )
    if review is None:
        return []
    advisory = review.get("advisory_findings")
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
