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

from agentmarshal.journal.actors import SOURCE_ACTORS_TABLE, _actor_git_identities
from agentmarshal.journal.contracts import JournalContractError, contract_sha256
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.records import _project_root_for
from agentmarshal.journal.status import TaskStatus
from agentmarshal.localstate import LocalState
from agentmarshal.project import project_file_path, read_project_file
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

    A ``project-actor`` source implies it — the id came out of the table.
    An override or a git identity can still *name* a declared actor, so
    declared-ness is otherwise tested on the id against the ``actors``
    keys of the project file the journal belongs to — the same one the
    recorder was resolved from. A project file that cannot be read
    declares nothing; the line then notes the recorder rather than
    failing (ADR-0022 section 3).
    """

    if record.get("recorded_by_source") == SOURCE_ACTORS_TABLE:
        return True
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
