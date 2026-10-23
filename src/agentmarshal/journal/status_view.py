"""The per-task ``status`` view rendered from journal evidence.

Each record type with a dedicated line registers a renderer in
``_RECORD_RENDERERS``; a record type without an entry falls back to the
generic id, type and time line. The view also renders the two additions
the local state brings — the overdue steps the process log reports
(ADR-0014 decision 9 as amended), printed on stdout after the
journal-derived detail, and the paths the journal, the process log and
the local state live at (decision 13), printed on stderr so stdout
stays what the documentation promises a parser.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TextIO, cast

from agentmarshal.journal.actors import _actor_git_identities
from agentmarshal.journal.contracts import JournalContractError, contract_sha256
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.records import _project_root_for
from agentmarshal.journal.status import (
    TaskStatus,
    TaskStatusError,
    load_task_status,
)
from agentmarshal.localstate import LocalState
from agentmarshal.project import (
    GitNotAvailableError,
    find_git_root,
    project_file_path,
    read_project_file,
)
from agentmarshal.settings import changes_required_threshold
from agentmarshal.steps import OpenStep, format_overdue

#: A renderer takes what the line needs — the project root for the
#: self-acceptance and self-acknowledgement checks, the journal root for
#: the actors table a recorder is checked against, and the record itself
#: — and returns the line. The dispatch in ``print_task_detail`` escapes
#: what it returns, so a renderer cannot forget to (ADR-0015 decision 5).
RecordRenderer = Callable[[Path, Path, dict[str, object]], str]


def _declared_commit_writers(project_root: Path, commit: str) -> set[str] | None:
    """Return the commit's declared author and committer names and emails.

    ``None`` when git cannot answer — an absent commit, a shallow clone, a
    directory that is not a repository. That is distinct from an answer of "no
    match", and the caller must keep the two apart.
    """

    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%an%n%ae%n%cn%n%ce", commit],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return {line.strip().casefold() for line in output.splitlines() if line.strip()}


def _is_self_accepted(project_root: Path, record: dict[str, object]) -> bool | None:
    """Whether the accepting party wrote the commit, or ``None`` if unknown.

    ADR-0007 calls self-acceptance the case an operator most needs to see. If an
    unanswerable git query were reported as "not self-accepted", the display
    would quietly lose exactly that — so unknown is carried through and said.
    """

    if "accepted_commit" not in record:
        return None
    writers = _declared_commit_writers(project_root, str(record["accepted_commit"]))
    if writers is None:
        return None
    return str(record["accepted_by"]).strip().casefold() in writers


def _is_self_acknowledged(
    project_root: Path, journal_root: Path, record: dict[str, object]
) -> bool | None:
    """Whether the acknowledging actor wrote the commit, or ``None`` if unknown.

    ADR-0021 decision 5 applies ADR-0007's rule to the acknowledgement: the
    mark is derived on display, never stored, and where git cannot read the
    commit the line says the mark was not checked — the same derivation
    ``_is_self_accepted`` makes. The recorder is a resolved value rather
    than a typed name, so its side of the comparison goes through
    ``_actor_git_identities`` — the actors table of the journal's own
    project file — plus the recorded name itself, matching the author and
    committer names and emails the commit declares.
    """

    writers = _declared_commit_writers(project_root, str(record["commit"]))
    if writers is None:
        return None
    identities = _actor_git_identities(_project_root_for(journal_root), record)
    recorded_by = record["recorded_by"]
    if isinstance(recorded_by, str) and recorded_by.strip():
        identities.add(recorded_by.strip().casefold())
    return not identities.isdisjoint(writers)


def _is_declared_recorder(journal_root: Path, record: dict[str, object]) -> bool:
    """Whether ``recorded_by`` names an actor the project file declares.

    "Declared" means in the project's actors table as it stands when
    ``status`` runs, for every source alike: a ``project-actor`` record
    says only where the id came from at write time — an actor removed
    from the table since is no longer declared — and an override or a
    git identity can still *name* a declared actor, so the id is tested
    against the ``actors`` keys of the project file the journal belongs
    to — the same one the recorder was resolved from. A project file
    that cannot be read declares nothing; the line then notes the
    recorder rather than failing (ADR-0022 section 3).
    """

    try:
        project = read_project_file(project_file_path(_project_root_for(journal_root)))
    except (OSError, ValueError):
        return False
    actors = project.get("actors")
    return isinstance(actors, dict) and record.get("recorded_by") in actors


def _recorder_clause(journal_root: Path, record: dict[str, object]) -> str:
    """The ``recorded_by=<actor>`` detail the schema-7 record lines share.

    A recorder that is not a declared actor is shown as such (ADR-0022
    section 3): the record stands, and the line says what it is.
    """

    note = (
        "" if _is_declared_recorder(journal_root, record) else " (not a declared actor)"
    )
    return f"recorded_by={record['recorded_by']}{note}"


def _render_review_line(
    _project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    findings = cast(list[object], record["findings"])
    advisory = cast(list[object], record.get("advisory_findings", []))
    binding = (
        f"reviewed_finding={record['reviewed_finding']}"
        if "reviewed_finding" in record
        else f"reviewed_commit={str(record['reviewed_commit'])[:7]}"
    )
    artifacts = cast(list[object], record.get("artifacts", []))
    artifact_detail = f" artifacts={len(artifacts)}" if artifacts else ""
    return (
        f"- {record['id']} review {record['created_at']} "
        f"{binding} "
        f"verdict={record['verdict']} findings={len(findings)} "
        f"advisory={len(advisory)}{artifact_detail}"
    )


def _render_acceptance_line(
    project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    checked = _is_self_accepted(project_root, record)
    marker = (
        ""
        if "accepted_finding" in record
        else {
            None: " self-acceptance-unchecked",
            True: " self-accepted",
        }.get(checked, "")
    )
    binding = (
        f"accepted_finding={record['accepted_finding']}"
        if "accepted_finding" in record
        else f"accepted_commit={str(record['accepted_commit'])[:7]}"
    )
    # The pause and operational forms carry no `findings` (ADR-0013
    # decisions 5 and 17); each names what it accepts where an acceptance
    # over findings names its findings.
    if "accepted_pause" in record:
        pause = cast(dict[str, object], record["accepted_pause"])
        subject = f"accepted_pause={pause['extension']}"
    elif "operational" in record:
        subject = "operational"
    else:
        findings = cast(list[object], record["findings"])
        subject = f"findings={','.join(str(finding) for finding in findings)}"
    return (
        f"- {record['id']} acceptance {record['created_at']} "
        f"{binding} "
        f"accepted_by={record['accepted_by']} "
        f"{subject} "
        f"reason={record['reason']}{marker}"
    )


def _render_completed_line(
    _project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    binding = (
        f"completed_finding={record['completed_finding']}"
        if "completed_finding" in record
        else f"completed_commit={str(record['completed_commit'])[:7]}"
    )
    return f"- {record['id']} completed {record['created_at']} {binding}"


def _render_finding_line(
    _project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    artifacts = cast(list[object], record["artifacts"])
    return (
        f"- {record['id']} finding {record['created_at']} "
        f"summary={record['summary']} artifacts={len(artifacts)}"
    )


def _render_abandoned_line(
    _project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    return (
        f"- {record['id']} abandoned {record['created_at']} reason={record['reason']}"
    )


def _render_reopened_line(
    _project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    return f"- {record['id']} reopened {record['created_at']} reason={record['reason']}"


def _render_amendment_line(
    _project_root: Path, _journal_root: Path, record: dict[str, object]
) -> str:
    return (
        f"- {record['id']} amendment {record['created_at']} reason={record['reason']}"
    )


def _render_check_line(
    _project_root: Path, journal_root: Path, record: dict[str, object]
) -> str:
    line = (
        f"- {record['id']} check {record['created_at']} "
        f"name={record['name']} result={record['result']} "
        f"commit={str(record['commit'])[:7]}"
    )
    if "failed_step" in record:
        line += f" failed_step={record['failed_step']}"
    return f"{line} {_recorder_clause(journal_root, record)}"


def _render_agreement_line(
    _project_root: Path, journal_root: Path, record: dict[str, object]
) -> str:
    return (
        f"- {record['id']} agreement {record['created_at']} "
        f"contract={str(record['contract'])[:7]} "
        f"{_recorder_clause(journal_root, record)}"
    )


def _render_acknowledgement_line(
    project_root: Path, journal_root: Path, record: dict[str, object]
) -> str:
    identification = (
        f"signature={record['signature']}"
        if "signature" in record
        else f"marker={record['marker']}"
    )
    checked = _is_self_acknowledged(project_root, journal_root, record)
    marker = {
        None: " self-acknowledgement not checked",
        True: " self-acknowledged",
    }.get(checked, "")
    return (
        f"- {record['id']} acknowledgement {record['created_at']} "
        f"commit={str(record['commit'])[:7]} file={record['file']} "
        f"{identification} {_recorder_clause(journal_root, record)} "
        f"reason={record['reason']}{marker}"
    )


def _render_ext_line(
    _project_root: Path, journal_root: Path, record: dict[str, object]
) -> str:
    return (
        f"- {record['id']} ext {record['created_at']} "
        f"kind={record['kind']} commit={str(record['commit'])[:7]} "
        f"payload_sha256={str(record['payload_sha256'])[:7]} "
        f"{_recorder_clause(journal_root, record)}"
    )


_RECORD_RENDERERS: dict[str, RecordRenderer] = {
    "review": _render_review_line,
    "acceptance": _render_acceptance_line,
    "completed": _render_completed_line,
    "finding": _render_finding_line,
    "abandoned": _render_abandoned_line,
    "reopened": _render_reopened_line,
    "amendment": _render_amendment_line,
    "check": _render_check_line,
    "agreement": _render_agreement_line,
    "acknowledgement": _render_acknowledgement_line,
    "ext": _render_ext_line,
}


def _contract_drift_line(journal_root: Path, task: TaskStatus) -> str | None:
    """One line when the contract drifted from its last pin, else ``None``.

    The pin is the `contract` hash carried by the task's latest `opened` or
    `amendment` record that carries one — the hash of the contract text that
    record established (ADR-0018 decision 1). A contract that cannot be read
    or hashed reads as no drift: the line is a reminder, never a failure.
    """

    pinned: str | None = None
    for record in task.records:
        if record["record_type"] in ("opened", "amendment"):
            contract = record.get("contract")
            if isinstance(contract, str):
                pinned = contract
    if pinned is None:
        return None
    contract_path = journal_root / "tasks" / task.task_id / "contract.md"
    try:
        current = contract_sha256(contract_path.read_bytes(), str(contract_path))
    except (JournalContractError, OSError):
        return None
    if current == pinned:
        return None
    return (
        f"Contract drifted from its pin {pinned[:7]} (now {current[:7]}); "
        "record the edit with amend"
    )


def _declared_list(entries: tuple[str, ...]) -> str:
    """The declared entries in their order, or the not-declared mark.

    An undeclared field is shown as not declared rather than omitted: the
    absence is stated, the same honesty the agreement line buys by existing
    — and the mark explains why the ran lines below carry no not-declared
    note for the role.
    """

    return ", ".join(entries) if entries else "(not declared)"


def _independence_list(rules: tuple[str, ...]) -> str:
    """The declared rules plus the rule the gate always checks.

    `reviewer-not-writer` runs for every candidate whether or not the
    header names it — the header naming it adds no second check — so the
    rules in force always include it: where the header did not name it,
    the line names it as always checked by the gate. A header declaring
    no `independence` still says so.
    """

    shown = list(rules) if rules else ["(not declared)"]
    if "reviewer-not-writer" not in rules:
        shown.append("reviewer-not-writer (always checked by the gate)")
    return ", ".join(shown)


def _shown_value(value: object) -> str:
    """The value as recorded, or the absent mark — never a guess.

    ADR-0018 decision 3 shows what ran; a field the record does not carry is
    shown as absent rather than derived from a neighbouring field — the
    vendor is ``usage.provider`` or absent, never parsed out of an actor
    string like ``openai/gpt-5``.
    """

    return value if isinstance(value, str) and value else "(absent)"


def _role_mark(actor: object, declared: tuple[str, ...]) -> str:
    """`` (not declared for the role)`` where the actor is outside the list.

    An actor that ran but is not in the contract's declared list is shown,
    not refused (ADR-0018 decision 3) — and only when the contract declares
    that role's list at all: with no list there is nothing to be outside of.
    Actor ids are exact labels — the actors table keys them exactly and the
    recorder check above compares exactly — so membership is exact string
    equality: an actor differing from every declared entry only in case or
    surrounding whitespace is not declared. An absent actor carries no
    mark: there is no name to check.
    """

    if not declared or not isinstance(actor, str) or not actor:
        return ""
    if actor in declared:
        return ""
    return " (not declared for the role)"


def _implementer_session_line(
    record: dict[str, object], declared: tuple[str, ...]
) -> str:
    """One ran line for an implementer session: actor, vendor, model, reason."""

    usage = record.get("usage")
    provider = usage.get("provider") if isinstance(usage, dict) else None
    line = (
        f"- implementer session {record['id']}: "
        f"actor={_shown_value(record.get('actor'))} "
        f"vendor={_shown_value(provider)} "
        f"model={_shown_value(record.get('model'))}"
    )
    fallback_reason = record.get("fallback_reason")
    if isinstance(fallback_reason, str) and fallback_reason:
        # The reason a run moved down the fallback list is shown, never
        # verified (ADR-0018 decision 3) — and only shown when the record
        # carries one: a run with none recorded claims none.
        line += f" fallback_reason={fallback_reason}"
    return line + _role_mark(record.get("actor"), declared)


def _review_ran_line(record: dict[str, object], declared: tuple[str, ...]) -> str:
    """One ran line for a review: the reviewer's actor, vendor and model."""

    reviewer = record.get("reviewer")
    if not isinstance(reviewer, dict):
        reviewer = {}
    actor = reviewer.get("actor")
    line = (
        f"- review {record['id']}: "
        f"actor={_shown_value(actor)} "
        f"vendor={_shown_value(reviewer.get('vendor'))} "
        f"model={_shown_value(reviewer.get('model'))}"
    )
    return line + _role_mark(actor, declared)


def _assignment_lines(task: TaskStatus) -> list[str]:
    """The assignment section's lines, or none when nothing is declared.

    ADR-0018 decision 3 shows the declared assignment next to what actually
    ran: the contract's `implementers` and `reviewers` in their declared
    order — the order is the fallback order — and the `independence` rules
    in force, then one line per implementer session (a session record whose
    `role` is `implementer`) and one per review, in the order the records
    stand. An empty ran side says so — `(none)` where its lines would
    stand, the mark the scope block prints for an empty scope — but only
    against a declared list: a side whose list the header does not declare
    already reads `(not declared)` on the declaration line. A contract
    declaring none of the three fields gets no section — its detail view
    stays byte for byte what it was.
    """

    contract = task.contract
    if not (contract.implementers or contract.reviewers or contract.independence):
        return []
    lines = [
        "Assignment:",
        f"- implementers: {_declared_list(contract.implementers)}",
        f"- reviewers: {_declared_list(contract.reviewers)}",
        f"- independence: {_independence_list(contract.independence)}",
    ]
    sessions = [
        _implementer_session_line(record, contract.implementers)
        for record in task.records
        if record.get("record_type") == "session"
        and record.get("role") == "implementer"
    ]
    reviews = [
        _review_ran_line(record, contract.reviewers)
        for record in task.records
        if record.get("record_type") == "review"
    ]
    if sessions:
        lines.extend(sessions)
    elif contract.implementers:
        lines.append("- implementer sessions: (none)")
    if reviews:
        lines.extend(reviews)
    elif contract.reviewers:
        lines.append("- reviews: (none)")
    return lines


def _agreement_line(journal_root: Path, task: TaskStatus) -> str | None:
    """One line on the task's recorded agreement, else ``None``.

    ADR-0018 decision 2 pairs the record with visibility: a task carrying
    no `agreement` record says so, instead of reading as agreement never
    asked for, and a latest agreement whose hash the contract has since
    left is said — against the contract's *current* hash, computed the
    way the drift line computes it, not against the pin. A contract that
    cannot be read or hashed reads as nothing to compare: the line is a
    reminder, never a failure.
    """

    agreements = [
        record for record in task.records if record["record_type"] == "agreement"
    ]
    if not agreements:
        return "No agreement with the contract is recorded"
    agreed = str(agreements[-1]["contract"])
    contract_path = journal_root / "tasks" / task.task_id / "contract.md"
    try:
        current = contract_sha256(contract_path.read_bytes(), str(contract_path))
    except (JournalContractError, OSError):
        return None
    if agreed == current:
        return None
    return (
        f"Recorded agreement {agreed[:7]} is for an earlier contract text "
        f"(now {current[:7]})"
    )


def _changes_required_count_line(journal_root: Path, task: TaskStatus) -> str | None:
    """One line with the task's ``changes_required`` count, else ``None``.

    ADR-0016 decision 4: the same count the gate's line carries since
    CR-168 — every review of the task's candidates, whatever commit it
    names; a review bound to a research finding (``reviewed_finding``,
    ADR-0009) is not a candidate's return and is not counted — computed
    over ``task.records`` with exactly the gate's definition (the counting
    block at the end of ``run_gate`` in ``gate.py``). The threshold is the
    project's ``review.changes_required_threshold`` read from the same
    root the gate reads it — the journal's own project root
    (``changes_required_threshold(journal_root.parents[1])`` in
    ``run_gate``), resolved through ``_project_root_for`` as the actors
    table already is; under a sidecar placement the host root the view
    also takes is a different project. An unreadable threshold is named
    on the line rather than refused. The line reports; it blocks nothing
    — and a task with no such verdict gets no line at all.
    """

    count = sum(
        1
        for record in task.records
        if record.get("record_type") == "review"
        and record.get("verdict") == "changes_required"
        and record.get("reviewed_finding") is None
    )
    if count == 0:
        return None
    try:
        threshold = changes_required_threshold(_project_root_for(journal_root))
    except (OSError, ValueError) as error:
        return (
            f"changes_required verdicts for {task.task_id}: {count} "
            f"(threshold unreadable: {error})"
        )
    if count >= threshold:
        return (
            f"changes_required verdicts for {task.task_id}: {count} "
            f"(threshold {threshold} reached — stop and revisit the "
            "contract)"
        )
    return (
        f"changes_required verdicts for {task.task_id}: {count} (threshold {threshold})"
    )


def _follow_up_state(journal_root: Path, task_id: str) -> str:
    """The follow-up task's state, or that the journal does not hold it.

    ``load_task_status`` raises for a task the journal does not hold —
    that is an ordinary answer here, not an error.
    """

    try:
        follow_up = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError):
        return "not held by the journal"
    return f"state: {follow_up.state}"


def _deferral_lines(journal_root: Path, task: TaskStatus) -> list[str]:
    """The open deferrals carried by the task's ``completed`` records.

    ADR-0016 decision 1: a deferral stays visible after the task closes.
    Each ``deferred`` entry of ``advisory_dispositions`` gets a line of
    its own naming the finding, its reason and — when present — the
    follow-up task with its state when the journal holds it, or that the
    journal does not hold it. ``fixed`` and ``rejected`` entries are
    counted on one line, not listed.
    """

    deferred: list[tuple[str, dict[str, object]]] = []
    fixed = 0
    rejected = 0
    for record in task.records:
        if record.get("record_type") != "completed":
            continue
        dispositions = record.get("advisory_dispositions")
        if not isinstance(dispositions, dict):
            continue
        for finding_id, entry in dispositions.items():
            if not isinstance(entry, dict):
                continue
            disposition = entry.get("disposition")
            if disposition == "deferred":
                deferred.append((str(finding_id), entry))
            elif disposition == "fixed":
                fixed += 1
            elif disposition == "rejected":
                rejected += 1
    if not deferred and not fixed and not rejected:
        return []
    lines = ["Deferrals:"]
    for finding_id, entry in deferred:
        line = f"- {finding_id}: reason={_shown_value(entry.get('reason'))}"
        follow_up = entry.get("follow_up")
        if isinstance(follow_up, str) and follow_up:
            line += (
                f" follow_up={follow_up} ({_follow_up_state(journal_root, follow_up)})"
            )
        lines.append(line)
    lines.append(f"fixed={fixed} rejected={rejected}")
    return lines


def _producing_session_line(task: TaskStatus) -> str | None:
    """One line naming the session that produced the reviewed commit.

    Proposal 036's read side: a reader of ``status`` can see whether the
    commit under review came from a run that finished. The commit is the
    task's latest review's ``reviewed_commit`` — the last review record
    wins, the same rule the gate holds an acceptance to, never searching
    backward for an older record that would justify a line; a review
    bound to a finding judges no commit and produces none. The producing
    session is an implementer session whose ``commit`` equals it — the
    whole 40-hex id, as the gate's range check compares session commits —
    the latest in stored order when several name it, the earlier ones
    counted. A task with no review, or none an implementer session
    names the commit of, gets no line: a candidate produced by a runner
    that wrote no session is shown as before (the disposition).
    """

    reviews = [
        record for record in task.records if record.get("record_type") == "review"
    ]
    if not reviews:
        return None
    commit = reviews[-1].get("reviewed_commit")
    if not isinstance(commit, str):
        return None
    sessions = [
        record
        for record in task.records
        if record.get("record_type") == "session"
        and record.get("role") == "implementer"
        and record.get("commit") == commit
    ]
    if not sessions:
        return None
    session = sessions[-1]
    line = (
        f"Reviewed commit {commit[:7]}: implementer session {session['id']} "
        f"actor={_shown_value(session.get('actor'))} "
        f"outcome={_shown_value(session.get('outcome'))}"
    )
    report_ready = session.get("report_ready")
    if isinstance(report_ready, bool):
        line += f" report_ready={'true' if report_ready else 'false'}"
    if session.get("outcome") != "implemented":
        line += " (did not end 'implemented')"
    if len(sessions) > 1:
        earlier = len(sessions) - 1
        noun = "session" if earlier == 1 else "sessions"
        line += f" (+{earlier} earlier implementer {noun})"
    return line


def records_absent_from_ref(
    journal_root: Path, task: TaskStatus, ref: str
) -> list[dict[str, object]]:
    """The task's records the working tree holds and ``ref`` does not.

    ``status --base``'s listing (proposal 035's disposition): a record is
    present at the ref when the ref's tree holds its path, so what prints
    is the record not yet published — names, not content: a record
    rewritten in place since still stands at the ref and is not listed.
    The ref resolves in the journal's own repository — under a sidecar
    placement the sidecar repository's ref, never the host's, because the
    records live there. A ref that does not resolve to a commit, and a
    repository that cannot answer, raise ``ValueError`` naming it.
    """

    try:
        repository = find_git_root(journal_root)
    except GitNotAvailableError as error:
        raise ValueError(f"cannot locate the journal's repository: {error}") from error
    if repository is None:
        raise ValueError(
            "the journal's repository is not a git worktree; "
            f"cannot resolve base {escape_for_display(ref)}"
        )
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repository,
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        raise ValueError(f"unknown base ref: {escape_for_display(ref)}")
    prefix = (
        (journal_root / "tasks" / task.task_id / "records")
        .relative_to(repository)
        .as_posix()
    )
    listing = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "-z",
            probe.stdout.decode("utf-8").strip(),
            "--",
            f":(literal){prefix}",
        ],
        cwd=repository,
        capture_output=True,
        check=False,
    )
    if listing.returncode != 0:
        detail = listing.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(
            f"cannot list records at {escape_for_display(ref)} in the "
            f"journal's repository: {escape_for_display(detail)}"
        )
    # NUL-separated, as the gate's listings are: a quoted name never equals
    # the raw one the working tree holds.
    present = {
        name
        for name in listing.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        if name
    }
    return [
        record
        for record in task.records
        if f"{prefix}/{record['id']}-{record['record_type']}.json" not in present
    ]


def print_task_detail(project_root: Path, task: TaskStatus, journal_root: Path) -> None:
    """Print one task's detail view: header, acceptance trail, scope, records."""

    # Every line built from a record or a contract goes through
    # ``escape_for_display``: a record a later read rule does not reach can
    # still carry a character that would forge a line or reorder text
    # (ADR-0015 decision 5).
    print(f"ID: {escape_for_display(task.task_id)}")
    print(f"Status: {task.state}")
    print(f"Title: {escape_for_display(task.contract.title)}")
    for acceptance in (
        record for record in task.records if record["record_type"] == "acceptance"
    ):
        accepted_by = escape_for_display(str(acceptance["accepted_by"]))
        if "accepted_pause" in acceptance:
            pause = cast(dict[str, object], acceptance["accepted_pause"])
            summary = (
                "Acceptance: accepted pause of extension "
                f"{escape_for_display(str(pause['extension']))} "
                f"by {accepted_by}"
            )
        elif "operational" in acceptance:
            summary = f"Acceptance: accepted operational CR by {accepted_by}"
        else:
            summary = f"Acceptance: accepted over findings by {accepted_by}"
        self_accepted = _is_self_accepted(project_root, acceptance)
        if "accepted_finding" in acceptance:
            summary += (
                f" (finding {escape_for_display(str(acceptance['accepted_finding']))})"
            )
        elif self_accepted is None:
            summary += (
                " (self-acceptance not checked: git cannot read "
                f"{escape_for_display(str(acceptance['accepted_commit'])[:7])} here)"
            )
        elif self_accepted:
            summary += (
                " (self-accepted: accepting party is a declared author or committer)"
            )
        print(summary)
    print("Scope:")
    if task.contract.scope:
        for path in task.contract.scope:
            print(f"- {escape_for_display(path)}")
    else:
        print("- (none)")
    # The declared assignment is contract-declared like the scope, so it
    # prints beside it — and `Records:` stays adjacent to the evidence it
    # lists (ADR-0018 decision 3). Each line is escaped like the record
    # lines: a value a later read rule does not reach can still carry a
    # refused character (ADR-0015 decision 5).
    for line in _assignment_lines(task):
        print(escape_for_display(line))
    print("Records:")
    for record in task.records:
        renderer = _RECORD_RENDERERS.get(cast(str, record["record_type"]))
        if renderer is None:
            print(
                f"- {escape_for_display(str(record['id']))} "
                f"{escape_for_display(str(record['record_type']))} "
                f"{escape_for_display(str(record['created_at']))}"
            )
        else:
            print(escape_for_display(renderer(project_root, journal_root, record)))
    agreement = _agreement_line(journal_root, task)
    if agreement is not None:
        print(escape_for_display(agreement))
    drift = _contract_drift_line(journal_root, task)
    if drift is not None:
        print(escape_for_display(drift))
    for line in _deferral_lines(journal_root, task):
        print(escape_for_display(line))
    count_line = _changes_required_count_line(journal_root, task)
    if count_line is not None:
        print(escape_for_display(count_line))
    # The read side of proposal 036's session-commit link — appended
    # last, as each derived line before it appended last: a candidate
    # no implementer session names keeps the view it had.
    producing = _producing_session_line(task)
    if producing is not None:
        print(escape_for_display(producing))


def print_paths(
    journal_root: Path,
    state: LocalState | None,
    local_state_error: str | None,
    stderr: TextIO,
) -> None:
    """Print the paths of the journal, the process log and the local state.

    ADR-0014 decision 13: ``status`` says where everything lives — one
    line per path on *stderr*, each escaped like other displayed text,
    so stdout stays what the documentation promises a parser. The
    resolved values print as given — in a sidecar they are the journal
    repository's, the host's never entering the call. A local state that
    cannot be resolved marks its two lines ``unavailable`` with the
    reason rather than failing the command; a missing ``log/`` directory
    is no error — its path prints and reads as no steps.
    """

    print(f"journal: {escape_for_display(str(journal_root))}", file=stderr)
    if state is None:
        reason = (
            f" ({escape_for_display(local_state_error)})" if local_state_error else ""
        )
        print(f"process log: unavailable{reason}", file=stderr)
        print(f"local state: unavailable{reason}", file=stderr)
        return
    print(f"process log: {escape_for_display(str(state.log))}", file=stderr)
    print(f"local state: {escape_for_display(str(state.root))}", file=stderr)


def print_overdue_steps(steps: Sequence[OpenStep]) -> None:
    """Print one line per overdue step, each naming this machine's log.

    The line carries the step id, the activity, the deadline and how long
    past it the step is, and says it comes from this machine's process
    log — the log is local to one machine (ADR-0014 decision 8), so a
    line that did not say so would read as task evidence it is not. The
    whole line goes through ``escape_for_display`` like every rendered
    line; a field written before the forgeable-text rule can still carry
    a character that would forge a line (ADR-0015 decision 5).
    """

    for step in steps:
        if step.overdue_by is None:
            continue
        print(
            escape_for_display(
                "Overdue step (this machine's process log): "
                f"step={step.step} activity={step.activity} "
                f"deadline={step.deadline} "
                f"past={format_overdue(step.overdue_by)}"
            )
        )
