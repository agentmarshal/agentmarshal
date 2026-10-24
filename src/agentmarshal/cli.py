"""Command-line interface for AgentMarshal."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from agentmarshal import (
    __version__,
    acknowledge,
    agree,
    extension_trust,
    outbox,
    record_check,
    record_ext,
    stages,
    steps,
)
from agentmarshal.doctor import run_doctor
from agentmarshal.extension_trust import _managed_directory
from agentmarshal.journal.acceptance import (
    AcceptanceError,
    accept_findings,
    accept_pause_or_operational,
)
from agentmarshal.journal.brief import build_brief
from agentmarshal.journal.capture import (
    CaptureError,
    CaptureLevel,
    _acknowledgement_mark,
    render_leak_hits,
    render_undecodable_files,
    review_capture_level_from_journal,
    scan_diff_for_leaks,
)
from agentmarshal.journal.complete import (
    LifecycleError,
    abandon_task,
    complete_findings_task,
    complete_task,
    record_commit_completion,
)
from agentmarshal.journal.contracts import contract_sha256
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.gate import (
    GateError,
    _resolve_commit,
    leak_scan_diff,
    markers_from_config,
    markers_from_tree,
    run_findings_gate,
    run_gate,
)
from agentmarshal.journal.gate_context import derive_gate_context
from agentmarshal.journal.open_task import (
    TaskOpenError,
    open_task,
    scope_warnings,
)
from agentmarshal.journal.placement import Placement, PlacementError, resolve_placement
from agentmarshal.journal.prune import (
    PruneError,
    delete_branches,
    delete_worktrees,
    report_branches,
    report_worktrees,
)
from agentmarshal.journal.records import (
    _SESSION_ACTIVITIES,
    JournalRecordError,
    create_amendment_record,
    create_finding_record,
    create_reopened_record,
    write_record,
)
from agentmarshal.journal.report import (
    ReportError,
    build_findings_report,
    build_report,
    format_findings_report,
    format_report,
)
from agentmarshal.journal.review import ReviewLaunchError, dry_run_review, launch_review
from agentmarshal.journal.session import SessionRecordError, record_session
from agentmarshal.journal.status import (
    TaskStatusError,
    list_task_statuses,
    load_task_for_record,
    load_task_status,
)
from agentmarshal.journal.status_view import (
    print_overdue_steps,
    print_paths,
    print_task_detail,
    records_absent_from_ref,
)
from agentmarshal.journal.submit_review import (
    ReviewSubmitError,
    reviewer_actor_note,
    submit_review,
)
from agentmarshal.journal.validate import validate_journal
from agentmarshal.localstate import LocalState, LocalStateError, local_state
from agentmarshal.migrate import JournalMigrationError, migrate_journal
from agentmarshal.project import (
    PROJECT_CONFIG_RELPATH,
    AgentMarshalProjectError,
    AlreadyInitializedError,
    find_git_root,
    find_project_root,
    initialize_project,
)
from agentmarshal.switches import (
    SWITCHES_RELPATH,
    read_switches,
    shared_extension_names,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentmarshal")
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser(
        "init", help="initialize AgentMarshal project metadata"
    )
    init_parser.add_argument(
        "--host",
        type=Path,
        help="initialize a sidecar journal over this git worktree",
    )
    subparsers.add_parser("doctor", help="check AgentMarshal project health")
    subparsers.add_parser("validate", help="validate the whole journal for integrity")
    open_parser = subparsers.add_parser("open", help="open a journal task")
    open_parser.add_argument("--title", help="task title")
    open_parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="path included in the task scope (repeatable)",
    )
    open_parser.add_argument(
        "--contract-file",
        type=Path,
        help="contract already written (header and body) to open the task from",
    )
    brief_parser = subparsers.add_parser(
        "brief", help="print an open task's implementer briefing"
    )
    brief_parser.add_argument("--task", required=True, help="task identifier")
    status_parser = subparsers.add_parser("status", help="show journal task status")
    status_parser.add_argument("task_id", nargs="?", help="task identifier")
    status_parser.add_argument(
        "--base",
        help=(
            "list the task's records present in the journal's working tree but "
            "absent from this ref (applies only to a named task)"
        ),
    )
    review_parser = subparsers.add_parser(
        "submit-review", help="record a task review verdict"
    )
    review_parser.add_argument("--task", required=True, help="task identifier")
    review_binding = review_parser.add_mutually_exclusive_group(required=True)
    review_binding.add_argument("--commit", help="reviewed commit SHA")
    review_binding.add_argument("--reviewed-finding", help="reviewed finding record id")
    review_parser.add_argument("--verdict", required=True, help="review verdict")
    review_parser.add_argument(
        "--finding",
        action="append",
        default=[],
        help="blocking finding id (repeatable)",
    )
    review_parser.add_argument(
        "--advisory-finding",
        action="append",
        default=[],
        help="non-blocking advisory finding id (repeatable)",
    )
    review_parser.add_argument("--role", required=True, help="reviewer role")
    review_parser.add_argument("--vendor", required=True, help="reviewer vendor")
    review_parser.add_argument("--model", required=True, help="reviewer model")
    review_parser.add_argument("--email", required=True, help="reviewer email")
    review_parser.add_argument(
        "--actor", help="declared reviewer actor id to record on the review"
    )
    review_parser.add_argument(
        "--prose",
        type=Path,
        help="file containing the reviewer's prose to preserve and pin",
    )
    accept_parser = subparsers.add_parser(
        "accept",
        help=(
            "record an operator acceptance — over a review's blocking "
            "findings, an extension's pause, or an operational CR"
        ),
    )
    accept_parser.add_argument("--task", required=True, help="task identifier")
    accept_binding = accept_parser.add_mutually_exclusive_group(required=True)
    accept_binding.add_argument(
        "--commit",
        help=(
            "the accepted commit — the reviewed commit SHA over findings; a "
            "revision resolved in the journal's repository with --pause or "
            "--operational"
        ),
    )
    accept_binding.add_argument("--accepted-finding", help="accepted finding record id")
    accept_parser.add_argument("--by", required=True, help="accepting party")
    accept_parser.add_argument("--reason", required=True, help="acceptance reason")
    accept_form = accept_parser.add_mutually_exclusive_group()
    accept_form.add_argument(
        "--pause",
        metavar="EXTENSION",
        help=(
            "accept an extension's pause — binds --commit, consults no "
            "review; EXTENSION must be a shared extension the working tree "
            "declares"
        ),
    )
    accept_form.add_argument(
        "--operational",
        action="store_true",
        help="accept an operational CR — binds --commit, no review is required",
    )
    accept_parser.add_argument(
        "--finding",
        action="append",
        default=[],
        help="assert a blocking finding id (repeatable; normally omitted)",
    )
    launch_parser = subparsers.add_parser(
        "review", help="run and record a read-only task review"
    )
    launch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="exercise the configured reviewer; records nothing",
    )
    # The shared review metadata is required for a recorded review and refused
    # for a dry run — except --actor, the one record flag a dry run accepts.
    # The selected binding decides whether --commit/--base apply.
    required_unless_dry_run = "required unless --dry-run"
    launch_parser.add_argument(
        "--task", help=f"task identifier ({required_unless_dry_run})"
    )
    launch_binding = launch_parser.add_mutually_exclusive_group()
    launch_binding.add_argument(
        "--commit",
        help=(
            "reviewed commit SHA (required for a commit review; does not apply to "
            "--dry-run)"
        ),
    )
    launch_binding.add_argument(
        "--reviewed-finding",
        help="reviewed finding record id (does not apply to --dry-run)",
    )
    launch_parser.add_argument(
        "--base",
        help=(
            "comparison base ref (required for a commit review; refused with "
            "--reviewed-finding and with --dry-run)"
        ),
    )
    launch_parser.add_argument(
        "--role", help=f"reviewer role ({required_unless_dry_run})"
    )
    launch_parser.add_argument(
        "--vendor", help=f"reviewer vendor ({required_unless_dry_run})"
    )
    launch_parser.add_argument(
        "--model",
        help="reviewer model (required unless --dry-run; a dry run needs it when "
        "the configured command names one)",
    )
    launch_parser.add_argument(
        "--email", help=f"reviewer email ({required_unless_dry_run})"
    )
    launch_parser.add_argument(
        "--actor",
        help=(
            "declared reviewer actor id to record on the review; a dry run "
            "accepts it and shows what it would record"
        ),
    )
    gate_parser = subparsers.add_parser(
        "gate", help="verify a merge candidate against the journal"
    )
    gate_parser.add_argument(
        "--task",
        default=None,
        help="task identifier (default: derived from the current branch name)",
    )
    gate_parser.add_argument(
        "--findings",
        action="store_true",
        help="gate the latest finding without a merge candidate",
    )
    gate_parser.add_argument(
        "--commit",
        default=None,
        help="candidate head SHA (default: the current HEAD)",
    )
    gate_parser.add_argument(
        "--base",
        default=None,
        help="merge target ref (default: the repository's default branch)",
    )
    gate_parser.add_argument(
        "--pipeline-sha",
        default=None,
        help="attested pipeline SHA (defaults to AGENTMARSHAL_PIPELINE_OK_SHA)",
    )
    gate_parser.add_argument(
        "--without-review",
        action="store_true",
        help=(
            "judge what does not depend on a review: when the candidate has no "
            "review record at all, report the review-bound checks as not "
            "examined instead of refusing. A candidate that has a review is "
            "judged exactly as it is without this flag"
        ),
    )
    gate_parser.add_argument(
        "--attestation",
        choices=("commit", "ci-required"),
        default="commit",
        help=(
            "pipeline attestation mode: 'commit' (default) requires "
            "--pipeline-sha to equal the candidate; 'ci-required' delegates "
            "attestation to the provider's required checks"
        ),
    )
    complete_parser = subparsers.add_parser(
        "complete", help="gate a candidate and record completion on success"
    )
    complete_parser.add_argument("--task", required=True, help="task identifier")
    complete_parser.add_argument("--commit", help="candidate head SHA")
    complete_parser.add_argument("--base", help="merge target ref")
    complete_parser.add_argument(
        "--target",
        help="the branch the candidate merges into — a pre-gate-stop pause "
        "refuses the completion while the candidate is not its ancestor",
    )
    complete_parser.add_argument(
        "--findings",
        action="store_true",
        help="complete against the latest finding without a candidate",
    )
    complete_parser.add_argument(
        "--disposition",
        action="append",
        default=[],
        metavar="ID=DISPOSITION[:REASON]",
        help="disposition for an advisory finding of the review the gate "
        "passed on: fixed, deferred:<reason> or rejected:<reason> — the "
        "reason is everything after the first colon (repeatable; every "
        "advisory finding of that review takes one)",
    )
    complete_parser.add_argument(
        "--follow-up",
        action="append",
        default=[],
        metavar="ID=TASK",
        help="follow-up task for a deferred advisory finding (repeatable)",
    )
    complete_parser.add_argument(
        "--pipeline-sha",
        default=None,
        help="attested pipeline SHA (defaults to AGENTMARSHAL_PIPELINE_OK_SHA)",
    )
    abandon_parser = subparsers.add_parser(
        "abandon", help="record abandonment of an open task"
    )
    abandon_parser.add_argument("--task", required=True, help="task identifier")
    abandon_parser.add_argument("--reason", required=True, help="abandonment reason")
    reopen_parser = subparsers.add_parser("reopen", help="reopen a completed task")
    reopen_parser.add_argument("--task", required=True, help="task identifier")
    reopen_parser.add_argument("--reason", required=True, help="reopening reason")
    amend_parser = subparsers.add_parser(
        "amend", help="record an amendment to an open task contract"
    )
    amend_parser.add_argument("--task", required=True, help="task identifier")
    amend_parser.add_argument("--reason", required=True, help="amendment reason")
    session_parser = subparsers.add_parser(
        "record-session", help="record attributed task work"
    )
    session_parser.add_argument("--task", required=True, help="task identifier")
    session_parser.add_argument("--role", required=True, help="worker role")
    session_parser.add_argument("--actor", required=True, help="worker identity")
    session_parser.add_argument(
        "--activity", required=True, help=", ".join(sorted(_SESSION_ACTIVITIES))
    )
    session_parser.add_argument("--outcome", required=True, help="work outcome")
    session_parser.add_argument("--input-tokens", type=int, default=0)
    session_parser.add_argument("--output-tokens", type=int, default=0)
    session_parser.add_argument("--cache-tokens", type=int, default=0)
    session_parser.add_argument("--usage-provider")
    session_parser.add_argument("--usage-method", choices=("reported", "measured"))
    session_parser.add_argument(
        "--commit", help="commit the session produced (any git revision)"
    )
    session_parser.add_argument("--model", help="model the session ran")
    session_parser.add_argument("--trace", help="external link to the run's trace")
    session_parser.add_argument("--cli-session", help="CLI session id a resume needs")
    session_parser.add_argument(
        "--report-ready",
        action="store_true",
        default=None,
        help="the run's report was finished",
    )
    session_parser.add_argument(
        "--fallback-reason", help="why the run moved down the fallback list"
    )
    session_parser.add_argument(
        "--started-at",
        help="session start, a UTC ISO-8601 timestamp (requires --ended-at)",
    )
    session_parser.add_argument(
        "--ended-at",
        help="session end, a UTC ISO-8601 timestamp (requires --started-at)",
    )
    session_parser.add_argument(
        "--resets-at",
        help="provider's stated reset time, a UTC ISO-8601 timestamp "
        "(a 'provider-limit' outcome only)",
    )
    session_parser.add_argument(
        "--cost-amount",
        help="session cost amount, a decimal string (requires --cost-currency "
        "and --cost-source)",
    )
    session_parser.add_argument(
        "--cost-currency",
        help="session cost currency, three uppercase ASCII letters (requires "
        "--cost-amount and --cost-source)",
    )
    session_parser.add_argument(
        "--cost-source",
        choices=("reported", "estimated"),
        help="session cost source (requires --cost-amount and --cost-currency)",
    )
    session_parser.add_argument(
        "--if-missing",
        action="store_true",
        help="write nothing and name the existing record when the task "
        "already holds a session with the same role, actor and activity",
    )
    finding_parser = subparsers.add_parser(
        "finding", help="record a hash-pinned research finding"
    )
    finding_parser.add_argument("--task", required=True, help="task identifier")
    finding_parser.add_argument("--summary", required=True, help="finding summary")
    finding_parser.add_argument(
        "--artifact",
        action="append",
        required=True,
        help="artifact as REF=SHA256 (repeatable)",
    )
    report_parser = subparsers.add_parser(
        "report", help="summarize task delegation economics"
    )
    report_parser.add_argument("--task", help="task identifier")
    report_parser.add_argument(
        "--findings",
        action="store_true",
        help="list the recorded finding classes and still-open deferrals "
        "instead of the economics report",
    )
    prune_parser = subparsers.add_parser(
        "prune", help="report local branches and worktrees for finished tasks"
    )
    prune_parser.add_argument(
        "--base",
        default="HEAD",
        help="ref used to judge merged branches (default: current HEAD)",
    )
    prune_parser.add_argument(
        "--delete", action="store_true", help="delete the artifacts reported eligible"
    )
    migrate_parser = subparsers.add_parser(
        "migrate-journal", help="convert a v1 journal into a new v2 journal"
    )
    migrate_parser.add_argument("--source", required=True, type=Path)
    migrate_parser.add_argument("--target", required=True, type=Path)
    migrate_parser.add_argument(
        "--lenient",
        action="store_true",
        help="tolerate pre-v1 header deltas: default safe fields, skip "
        "unreconstructable records, and report each",
    )
    leak_scan_parser = subparsers.add_parser(
        "leak-scan",
        help="scan a candidate diff's added content for secrets/markers "
        "(best-effort, provider-neutral)",
    )
    leak_scan_parser.add_argument(
        "--base", required=True, help="merge target ref (the comparison base)"
    )
    leak_scan_parser.add_argument(
        "--commit", required=True, help="candidate head ref to scan"
    )
    leak_scan_parser.add_argument(
        "--task",
        help="task identifier to read acknowledgements from "
        "(default: every task of the journal)",
    )
    outbox.register(subparsers)
    steps.register(subparsers)
    stages.register(subparsers)
    extension_trust.register(subparsers)
    acknowledge.register(subparsers)
    agree.register(subparsers)
    record_check.register(subparsers)
    record_ext.register(subparsers)
    return parser


def _run_init(host: Path | None, stderr: TextIO) -> int:
    try:
        initialized = initialize_project(Path.cwd(), host=host)
    except AlreadyInitializedError as error:
        print(error, file=stderr)
        return 1
    except AgentMarshalProjectError as error:
        print(error, file=stderr)
        return 1

    print(f"Initialized AgentMarshal project at {initialized.project_root}")
    # The convention is stated either way. An operator whose outbox could not be
    # created still needs to know it was meant to be there, and why it is not —
    # silence would leave them believing nothing was supposed to happen.
    print(
        f"Findings about AgentMarshal itself go in {initialized.outbox} "
        "— see its README"
    )
    if not initialized.outbox_created:
        print(
            f"warning: could not create {initialized.outbox}: "
            f"{initialized.outbox_error}",
            file=stderr,
        )
    print("Before the first governed task, configure these preconditions:")
    print(
        "- Provider: disable squash and rebase merges; either rewrites the "
        "reviewed SHA, so review evidence no longer binds to the merged commit."
    )
    print(
        "- Harness: set AGENTMARSHAL_ACTOR for each agent; without it, an "
        "agent's records resolve to the invoking git identity."
    )
    print(
        "- Reviewer: configure AGENTMARSHAL_REVIEWER_CMD when using "
        "agentmarshal review; without it, an automated review cannot launch."
    )
    print(
        "- CI: install a workflow that invokes agentmarshal validate; without "
        "it, journal integrity is not checked before merge."
    )
    return 0


def _placement(
    command: str, stderr: TextIO, *, require_host: bool = False
) -> Placement | None:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            f"agentmarshal {command} must be run inside an initialized project",
            file=stderr,
        )
        return None
    try:
        return resolve_placement(project_root, require_host=require_host)
    except PlacementError as error:
        # The message can carry a value the tool did not write — a host
        # path from project.json, git's own error text — so it is escaped
        # the way a transcript line is: nothing it carries can add a line
        # or reorder what prints here.
        print(escape_for_display(str(error)), file=stderr)
        return None


def _run_doctor() -> int:
    results = run_doctor()
    for result in results:
        if result.ok:
            status = "OK"
        elif result.precondition:
            # Not a failure: something only the operator can establish, which
            # this command reports rather than judges. Printing FAIL here would
            # be the very habit this check exists to break.
            status = "TODO"
        else:
            status = "FAIL"
        print(f"{status}: {result.name} — {result.detail}")
    unmet = [result for result in results if not result.ok]
    broken = [result for result in unmet if not result.precondition]
    if unmet:
        parts = []
        if broken:
            parts.append(f"{len(broken)} check(s) failed")
        todo = len(unmet) - len(broken)
        if todo:
            parts.append(f"{todo} precondition(s) left to the operator")
        print("Summary: " + ", ".join(parts))
        return 1 if broken else 0
    print(f"Summary: all {len(results)} checks passed")
    return 0


def _run_open(args: argparse.Namespace, stderr: TextIO) -> int:
    if args.contract_file is not None:
        if args.title is not None or args.scope:
            print(
                "open --contract-file cannot be combined with --title or --scope",
                file=stderr,
            )
            return 1
    elif args.title is None:
        print("open requires --title or --contract-file", file=stderr)
        return 1
    placement = _placement("open", stderr, require_host=True)
    if placement is None:
        return 1
    try:
        opened_task = open_task(
            placement.project_root,
            args.title,
            args.scope,
            contract_file=args.contract_file,
        )
    except TaskOpenError as error:
        print(error, file=stderr)
        return 1
    for warning in scope_warnings(placement.host_root, list(opened_task.scope)):
        print(f"warning: {warning}", file=stderr)
    if opened_task.replaced_id is not None:
        print(
            f"contract id {opened_task.replaced_id!r} replaced with the "
            f"assigned task id {opened_task.task_id!r}",
            file=stderr,
        )
    print(opened_task.contract_path)
    print(opened_task.record_path)
    return 0


def _run_brief(task_id: str, stderr: TextIO) -> int:
    placement = _placement("brief", stderr)
    if placement is None:
        return 1
    try:
        briefing = build_brief(
            placement.journal_root, task_id, host_root=placement.host_root
        )
    except (OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    sys.stdout.write(briefing)
    return 0


def _run_submit_review(args: argparse.Namespace, stderr: TextIO) -> int:
    placement = _placement("submit-review", stderr)
    if placement is None:
        return 1
    # argparse enforces exactly one of --commit / --reviewed-finding; --finding
    # keeps its one meaning, a blocking finding id, under either binding.
    try:
        if args.prose is not None:
            try:
                prose_capture_level = review_capture_level_from_journal(
                    placement.journal_root
                )
            except (CaptureError, ValueError) as error:
                raise ReviewSubmitError(str(error)) from error
            if prose_capture_level is not CaptureLevel.COMMIT:
                raise ReviewSubmitError(
                    "review prose cannot be kept at capture level "
                    f"{prose_capture_level.value!r}; set "
                    'capture.overrides.reviews = "commit" to permit it'
                )
        prose = args.prose.read_bytes() if args.prose is not None else None
        submitted = submit_review(
            placement.journal_root,
            args.task,
            args.commit,
            args.verdict,
            args.role,
            args.vendor,
            args.model,
            args.email,
            args.finding,
            args.advisory_finding,
            reviewed_finding=args.reviewed_finding,
            prose=prose,
            reviewer_actor=args.actor,
        )
    except (OSError, ReviewSubmitError) as error:
        print(error, file=stderr)
        return 1
    print(submitted.record_path)
    if submitted.actor_note is not None:
        print(submitted.actor_note, file=stderr)
    return 0


def _run_accept(args: argparse.Namespace, stderr: TextIO) -> int:
    # argparse enforces exactly one of --commit / --accepted-finding, and
    # that --pause and --operational never combine; a new form binds
    # --commit alone and takes none of the findings form's flags — the
    # refusal is pure argument checking and can never write.
    if args.pause is not None or args.operational:
        form = "--pause" if args.pause is not None else "--operational"
        refused = [
            flag
            for flag, given in (
                ("--accepted-finding", args.accepted_finding is not None),
                ("--finding", bool(args.finding)),
            )
            if given
        ]
        if refused:
            print(
                f"accept {form} cannot be combined with " + " or ".join(refused),
                file=stderr,
            )
            return 1
        if args.commit is None:
            # Unreachable while the binding group is required — an absent
            # --commit means --accepted-finding was given, refused above —
            # but it is the binding rule the new forms are held to.
            print(f"accept {form} requires --commit", file=stderr)
            return 1
        placement = _placement("accept", stderr)
        if placement is None:
            return 1
        try:
            record_path = accept_pause_or_operational(
                placement.journal_root,
                placement.project_root,
                args.task,
                args.commit,
                args.by,
                args.reason,
                accepted_pause=args.pause,
                operational=args.operational,
            )
        except AcceptanceError as error:
            print(error, file=stderr)
            return 1
        print(record_path)
        return 0
    placement = _placement("accept", stderr)
    if placement is None:
        return 1
    # argparse enforces exactly one of --commit / --accepted-finding; --finding
    # keeps its one meaning, an asserted blocking finding id.
    try:
        record_path = accept_findings(
            placement.journal_root,
            args.task,
            args.commit,
            args.by,
            args.reason,
            args.finding or None,
            accepted_finding=args.accepted_finding,
        )
    except AcceptanceError as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    return 0


def _run_review(args: argparse.Namespace, stderr: TextIO) -> int:
    if args.dry_run:
        ignored = [
            flag
            for flag, value in (
                ("--task", args.task),
                ("--commit", args.commit),
                ("--base", args.base),
                ("--role", args.role),
                ("--vendor", args.vendor),
                ("--email", args.email),
                ("--reviewed-finding", args.reviewed_finding),
            )
            if value is not None
        ]
        if ignored:
            print(
                "review --dry-run judges the configured command, not any work: "
                + ", ".join(ignored)
                + " does not apply",
                file=stderr,
            )
            return 1
        placement = _placement("review", stderr, require_host=True)
        if placement is None:
            return 1
        try:
            tree, diagnostics_note = dry_run_review(
                placement.host_root,
                args.model,
                journal_root=placement.journal_root,
                reviewer_actor=args.actor,
            )
        except ReviewLaunchError as error:
            print(f"dry run failed: {error}", file=stderr)
            return 1
        print(
            f"dry run: the command ran against {tree}; its output has a "
            "parseable verdict; nothing was recorded"
        )
        if args.actor is not None:
            print(
                f"dry run: would record reviewer actor {escape_for_display(args.actor)}"
            )
            actor_note = reviewer_actor_note(placement.journal_root, args.actor)
            if actor_note is not None:
                print(actor_note, file=stderr)
        if diagnostics_note is not None:
            print(diagnostics_note, file=stderr)
        return 0
    required = {
        "--task": args.task,
        "--role": args.role,
        "--vendor": args.vendor,
        "--model": args.model,
        "--email": args.email,
    }
    if args.reviewed_finding is None:
        required.update({"--commit": args.commit, "--base": args.base})
    elif args.base is not None:
        print("review --base applies only to --commit", file=stderr)
        return 1
    missing = [flag for flag, value in required.items() if value is None]
    if missing:
        print("review: required unless --dry-run: " + ", ".join(missing), file=stderr)
        return 1
    placement = _placement("review", stderr, require_host=args.reviewed_finding is None)
    if placement is None:
        return 1
    try:
        submitted = launch_review(
            placement.host_root,
            args.task,
            args.commit,
            args.base,
            args.role,
            args.vendor,
            args.model,
            args.email,
            journal_root=placement.journal_root if placement.is_sidecar else None,
            reviewed_finding=args.reviewed_finding,
            reviewer_actor=args.actor,
        )
    except ReviewLaunchError as error:
        print(error, file=stderr)
        return 1
    if submitted.artifact_ref is not None:
        # The record pins the reasoning; say where, on stderr, so stdout
        # stays the record path a caller can read.
        print(f"reviewer prose pinned: {submitted.artifact_ref}", file=stderr)
    if submitted.diagnostics_note is not None:
        print(submitted.diagnostics_note, file=stderr)
    if submitted.prose_note is not None:
        print(submitted.prose_note, file=stderr)
    if submitted.actor_note is not None:
        print(submitted.actor_note, file=stderr)
    print(submitted.record_path)
    return 0


def _run_validate(stderr: TextIO) -> int:
    placement = _placement("validate", stderr)
    if placement is None:
        return 1
    report = validate_journal(placement.project_root)
    for line in report.lines:
        print(line)
    if not report.passed:
        print("validate: journal invalid", file=stderr)
        return 1
    print("validate: passed")
    return 0


def _run_gate(args: argparse.Namespace, stderr: TextIO) -> int:
    if args.findings and args.without_review:
        print(
            "gate --without-review judges a candidate's review; the findings "
            "lane has no candidate and already reports what it did not examine",
            file=stderr,
        )
        return 1
    if args.findings and (args.commit is not None or args.base is not None):
        print(
            "gate: --findings is mutually exclusive with --commit and --base",
            file=stderr,
        )
        return 1
    if args.findings and not args.task:
        print("gate: --task is required with --findings", file=stderr)
        return 1
    placement = _placement("gate", stderr, require_host=not args.findings)
    if placement is None:
        return 1
    if not args.findings and placement.advisory_notice is not None:
        print(placement.advisory_notice)
    project_root = placement.host_root
    if args.findings:
        # ADR-0009 Decision 4: in a sidecar this lane decides rather than
        # advises, and its transcript states the placement it decided under.
        if placement.is_sidecar:
            print(placement.evidence_line)
        try:
            report = run_findings_gate(placement.journal_root, args.task)
        except GateError as error:
            print(error, file=stderr)
            return 1
        for line in report.lines:
            print(line)
        if not report.passed:
            print("gate: findings refused", file=stderr)
            return 1
        print("gate: findings passed")
        return 0
    pipeline_sha = args.pipeline_sha or os.environ.get("AGENTMARSHAL_PIPELINE_OK_SHA")
    if placement.is_sidecar and not args.task:
        # Deriving the task from a branch name is a convenience of the embedded
        # placement, where the branch and the journal are the same repository.
        # In a sidecar the branch belongs to the host, and a host branch named
        # feat/CR-001-x would silently bind to this journal's unrelated CR-001
        # — the cross-journal conflation ADR-0008 Decision 2 rules out.
        print(
            "gate: --task is required in a sidecar; the host's branch names a "
            "task in the host's own numbering, not this journal's",
            file=stderr,
        )
        return 1
    try:
        context = derive_gate_context(project_root, args.task, args.commit, args.base)
        report = run_gate(
            project_root,
            context.task,
            context.commit,
            context.base,
            pipeline_sha,
            attestation=args.attestation,
            journal_root=placement.journal_root if placement.is_sidecar else None,
            review_required=not args.without_review,
        )
    except GateError as error:
        print(error, file=stderr)
        if placement.is_sidecar and not args.findings:
            print(
                "gate: the sidecar could not evaluate this candidate — check "
                "that the commit and base exist in the configured host",
                file=stderr,
            )
        return 1
    for line in report.lines:
        print(line)
    if not report.passed:
        # The refusal is part of the transcript, so it carries the same
        # statement the pass does. "gate: refused" is the authority's wording
        # and a sidecar has none to exercise.
        print(
            "gate: advisory checks refused; decides no merge"
            if placement.is_sidecar
            else "gate: refused",
            file=stderr,
        )
        return 1
    if placement.is_sidecar and report.review_not_examined:
        print(
            "gate: advisory checks passed what they examined; the review was "
            "not examined; decides no merge"
        )
    elif placement.is_sidecar:
        print("gate: advisory checks passed; decides no merge")
    elif report.review_not_examined:
        print("gate: passed what it examined; the review was not examined")
    else:
        print("gate: passed")
    return 0


def _candidate_merged(project_root: Path, commit: str, target: str) -> bool:
    """Whether the candidate commit is already an ancestor of the target.

    ``git merge-base --is-ancestor`` in the journal's repository, the
    references resolved with the gate's own ``_resolve_commit`` — the
    way ``complete`` resolves them for its gate check. ADR-0013 decision
    2: a ``pre-gate-stop`` pause applies inside ``complete`` only while
    the candidate is not yet merged into the target branch —
    ``--target``, distinct from ``--base``, which stays the merge base
    the gate diffs against (a merge wrapper passes the pre-merge merge
    base even after the merge). An answer the check cannot produce — a
    reference that will not resolve, a git that will not run — reads as
    not merged: the pause stands rather than being silently lifted.
    """

    try:
        resolved_commit = _resolve_commit(project_root, commit)
        resolved_target = _resolve_commit(project_root, target)
        answer = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                resolved_commit,
                resolved_target,
            ],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except (GateError, OSError):
        return False
    return answer.returncode == 0


def _run_complete(args: argparse.Namespace, stderr: TextIO) -> int:
    if args.findings and (args.commit is not None or args.base is not None):
        print(
            "complete: --findings is mutually exclusive with --commit and --base",
            file=stderr,
        )
        return 1
    if args.findings and args.target is not None:
        print("complete: --findings takes no --target", file=stderr)
        return 1
    if not args.findings and (args.commit is None or args.base is None):
        print(
            "complete: --commit and --base are required without --findings", file=stderr
        )
        return 1
    if args.findings and (args.disposition or args.follow_up):
        print("complete: --findings takes no dispositions", file=stderr)
        return 1
    placement = _placement("complete", stderr, require_host=not args.findings)
    if placement is None:
        return 1
    if not args.findings and placement.advisory_notice is not None:
        print(placement.advisory_notice)
    if args.findings and placement.is_sidecar:
        print(placement.evidence_line)
    pipeline_sha = args.pipeline_sha or os.environ.get("AGENTMARSHAL_PIPELINE_OK_SHA")
    # The local state the stage runner needs — resolved only on the lane
    # that invokes stages (the embedded candidate lane); the findings lane
    # and the sidecar run none.
    state: LocalState | None = None
    try:
        if args.findings:
            result = complete_findings_task(placement.journal_root, args.task)
            report = result.report
            record_path = result.record_path
        elif placement.is_sidecar:
            load_task_for_record(placement.journal_root, args.task, "completed")
            report = run_gate(
                placement.host_root,
                args.task,
                args.commit,
                args.base,
                pipeline_sha,
                journal_root=placement.journal_root,
            )
            record_path = None
            if report.passed:
                record_path = record_commit_completion(
                    placement.journal_root,
                    args.task,
                    report.resolved_commit,
                    resolved_review=report.resolved_review,
                    dispositions=args.disposition,
                    follow_ups=args.follow_up,
                )
        else:
            # The task's open state is established first, so a closed
            # task's refusal still precedes any extension work — then the
            # declared pre-gate stages run, the same run `stage run`
            # performs, before the gate check and before anything is
            # written (ADR-0013 decision 2).
            load_task_for_record(placement.journal_root, args.task, "completed")
            # The refs are resolved the gate's own way before any
            # extension work: a bad ref keeps the refusal complete gives
            # it today, and the runner — invoked quiet — is handed the
            # resolved SHAs so its own diagnostics can only be about the
            # extension machinery.
            resolved_commit = _resolve_commit(placement.project_root, args.commit)
            resolved_base = _resolve_commit(placement.project_root, args.base)
            state = local_state(placement)
            stage_run = stages.run_stages(
                placement,
                state,
                args.task,
                resolved_commit,
                resolved_base,
                "pre-gate",
                stderr,
                quiet=True,
            )
            if stage_run.status == 3:
                if args.target is not None and _candidate_merged(
                    placement.project_root, resolved_commit, args.target
                ):
                    for entry in stage_run.pauses:
                        print(
                            "complete: WARNING: extension at pre-gate-stop — "
                            f"{entry} — the candidate is already merged into "
                            "the target",
                            file=stderr,
                        )
                else:
                    print(
                        "complete: the completion is paused before the gate — "
                        + "; ".join(stage_run.pauses),
                        file=stderr,
                    )
                    return 3
            elif stage_run.status != 0:
                print(
                    "complete: pre-gate stage run refused; task not completed",
                    file=stderr,
                )
                return stage_run.status
            result = complete_task(
                placement.project_root,
                args.task,
                resolved_commit,
                resolved_base,
                pipeline_sha,
                dispositions=args.disposition,
                follow_ups=args.follow_up,
            )
            report = result.report
            record_path = result.record_path
    except (
        GateError,
        JournalRecordError,
        LifecycleError,
        LocalStateError,
        OSError,
        TaskStatusError,
        ValueError,
    ) as error:
        print(error, file=stderr)
        if (
            placement.is_sidecar
            and not args.findings
            and not isinstance(error, LifecycleError)
        ):
            print(
                "complete: the sidecar could not evaluate this candidate — check "
                "that the commit and base exist in the configured host",
                file=stderr,
            )
        return 1
    for line in report.lines:
        print(line)
    if record_path is None:
        if args.findings:
            message = "complete: findings gate refused; task not completed"
        elif placement.is_sidecar:
            message = "complete: advisory checks refused; nothing recorded"
        else:
            message = "complete: gate refused; task not completed"
        print(message, file=stderr)
        return 1
    print(record_path)
    if args.findings:
        print("completed through findings")
    elif placement.is_sidecar:
        print("completed after advisory checks; decides no merge")
    else:
        print("completed")
    if state is not None:
        # The declared post-gate stages run once the ``completed`` record
        # exists — the same run `stage run` performs, its status informing
        # nothing: a post-gate stage cannot pause, and its outcome does
        # not change completion's verdict (ADR-0013 decision 2). The
        # resolved SHAs are the pre-gate run's, so the notification
        # reports on the commit that was gated.
        stages.run_stages(
            placement,
            state,
            args.task,
            resolved_commit,
            resolved_base,
            "post-gate",
            stderr,
            quiet=True,
        )
    return 0


def _run_finding(args: argparse.Namespace, stderr: TextIO) -> int:
    placement = _placement("finding", stderr)
    if placement is None:
        return 1
    artifacts: list[dict[str, str]] = []
    for value in args.artifact:
        reference, separator, digest = value.rpartition("=")
        if not separator or not reference or not digest:
            print("artifact must be REF=SHA256", file=stderr)
            return 1
        artifacts.append({"ref": reference, "hash": digest})
    try:
        load_task_for_record(placement.journal_root, args.task, "finding")
        record = create_finding_record(args.task, __version__, args.summary, artifacts)
        record_path = write_record(placement.journal_root, args.task, record)
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    return 0


def _run_abandon(args: argparse.Namespace, stderr: TextIO) -> int:
    placement = _placement("abandon", stderr)
    if placement is None:
        return 1
    try:
        record_path = abandon_task(placement.project_root, args.task, args.reason)
    except LifecycleError as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print("abandoned")
    return 0


def _run_reopen(args: argparse.Namespace, stderr: TextIO) -> int:
    placement = _placement("reopen", stderr)
    if placement is None:
        return 1
    if not args.reason.strip():
        print("reopen reason must not be empty", file=stderr)
        return 1
    journal_root = placement.journal_root
    try:
        load_task_for_record(journal_root, args.task, "reopened")
        record = create_reopened_record(args.task, __version__, args.reason)
        record_path = write_record(journal_root, args.task, record)
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print("reopened")
    return 0


def _run_amend(args: argparse.Namespace, stderr: TextIO) -> int:
    placement = _placement("amend", stderr)
    if placement is None:
        return 1
    if not args.reason.strip():
        print("amend reason must not be empty", file=stderr)
        return 1
    journal_root = placement.journal_root
    try:
        load_task_for_record(journal_root, args.task, "amendment")
        # The amendment pins the contract as it stands at this moment — the
        # journal repository's copy, in a sidecar as here (ADR-0018 decision
        # 1). A contract that does not parse was refused by the load above,
        # and bytes that do not decode are refused by the hash itself.
        contract_path = journal_root / "tasks" / args.task / "contract.md"
        contract_hash = contract_sha256(contract_path.read_bytes(), str(contract_path))
        record = create_amendment_record(
            args.task, __version__, args.reason, contract=contract_hash
        )
        record_path = write_record(journal_root, args.task, record)
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    return 0


def _run_record_session(args: argparse.Namespace, stderr: TextIO) -> int:
    if args.usage_provider is None and args.usage_method is not None:
        print(
            "--usage-provider is required when --usage-method is supplied", file=stderr
        )
        return 1
    if args.usage_method is None and args.usage_provider is not None:
        print(
            "--usage-method is required when --usage-provider is supplied", file=stderr
        )
        return 1
    placement = _placement(
        "record-session", stderr, require_host=args.commit is not None
    )
    if placement is None:
        return 1
    commit = None
    if args.commit is not None:
        try:
            commit = _resolve_commit(placement.host_root, args.commit)
        except GateError as error:
            print(error, file=stderr)
            return 1
    try:
        recorded = record_session(
            placement.journal_root,
            args.task,
            args.role,
            args.actor,
            args.activity,
            args.outcome,
            args.input_tokens,
            args.output_tokens,
            args.cache_tokens,
            usage_provider=args.usage_provider,
            usage_method=args.usage_method,
            commit=commit,
            model=args.model,
            trace=args.trace,
            cli_session=args.cli_session,
            report_ready=args.report_ready,
            fallback_reason=args.fallback_reason,
            started_at=args.started_at,
            ended_at=args.ended_at,
            resets_at=args.resets_at,
            cost_amount=args.cost_amount,
            cost_currency=args.cost_currency,
            cost_source=args.cost_source,
            if_missing=args.if_missing,
        )
    except SessionRecordError as error:
        print(error, file=stderr)
        return 1
    if recorded.existing_id is not None:
        print(f"already recorded: {recorded.existing_id}")
    else:
        print(recorded.record_path)
    return 0


def _run_report(task_id: str | None, stderr: TextIO, findings: bool) -> int:
    placement = _placement("report", stderr)
    if placement is None:
        return 1
    print(placement.evidence_line, file=stderr)
    try:
        if findings:
            lines = format_findings_report(
                build_findings_report(placement.journal_root, task_id)
            )
        else:
            lines = format_report(
                build_report(placement.journal_root, task_id),
                include_summary=task_id is None,
            )
    except ReportError as error:
        print(error, file=stderr)
        return 1
    for line in lines:
        print(line)
    return 0


def _print_switched_off(project_root: Path, stderr: TextIO) -> None:
    """Print one line per shared extension the working tree switches off.

    ADR-0013 decision 17's ``status`` half: ``switched off: <name>
    since <task> (<reason>)``, one line per shared extension the
    working tree's ``switches.toml`` switches off — the file ``doctor``
    reads, through the same ``read_switches``, against the names
    ``shared_extension_names`` enumerates for the working tree's
    ``.agentmarshal/extensions/``, in the enumeration's sorted order.
    Every value the file carries is escaped for display. Absence is
    decided before the names are enumerated: no entry at the file's
    path — asked by ``lstat``, so a dangling link is an entry and takes
    the file's own read the way ``doctor``'s read reports it — is every
    extension on and prints nothing. A file the read refuses, or a
    names enumeration that itself fails, is named on one
    ``switches: unavailable (<reason>)`` line — a report beside the
    paths, never a failure, and stdout is untouched.
    """

    switches_path = project_root / SWITCHES_RELPATH
    try:
        switches_path.lstat()
    except FileNotFoundError:
        return
    except OSError:
        # An entry that cannot be lstat'ed is not absent; the file's
        # own read names the trouble the way doctor's read does.
        pass
    try:
        names = shared_extension_names(_managed_directory(project_root))
        switches = read_switches(switches_path, names)
    except Exception as error:
        print(
            f"switches: unavailable ({escape_for_display(str(error))})",
            file=stderr,
        )
        return
    for name in sorted(switches):
        switch = switches[name]
        if switch.state == "off":
            print(
                escape_for_display(
                    f"switched off: {name} since {switch.task} ({switch.reason})"
                ),
                file=stderr,
            )


def _run_status(task_id: str | None, base: str | None, stderr: TextIO) -> int:
    if base is not None and task_id is None:
        print("status --base applies only to a named task", file=stderr)
        return 1
    placement = _placement("status", stderr)
    if placement is None:
        return 1
    print(placement.evidence_line, file=stderr)
    journal = placement.journal_root
    # ADR-0014 decision 13: where everything lives prints once on stderr,
    # so stdout stays what the documentation promises a parser and the
    # lines survive an empty list and a failed task lookup alike. A local
    # state that cannot be resolved degrades its two lines to
    # "unavailable" rather than failing a command that needed no git
    # before.
    state: LocalState | None = None
    state_error: str | None = None
    try:
        state = local_state(placement)
    except LocalStateError as error:
        state_error = str(error)
    print_paths(journal, state, state_error, stderr)
    # ADR-0013 decision 17's status half goes beside the paths: the
    # switched-off lines are owed in every case print_paths printed —
    # before the listing's "No tasks." or the view's lookup can return.
    _print_switched_off(placement.project_root, stderr)
    now = datetime.now(UTC)
    # The log is read once for the run — not once per task — and the
    # step events are indexed by task once, so each task's lookup scans
    # only its own slice. A log that cannot be read is named on stderr
    # and reads as no steps.
    events = (
        steps.read_process_events(state, stderr, "status") if state is not None else []
    )
    events_by_task = steps.step_events_by_task(events)
    try:
        if task_id is None:
            tasks = list_task_statuses(journal)
            if not tasks:
                print("No tasks.")
                return 0
            for task in tasks:
                overdue = any(
                    step.overdue_by is not None
                    for step in steps.open_steps(
                        task.task_id,
                        task.records,
                        events_by_task.get(task.task_id, ()),
                        now=now,
                    )
                )
                marker = "\toverdue-step" if overdue else ""
                print(
                    f"{escape_for_display(task.task_id)}\t{task.state}"
                    f"\t{escape_for_display(task.contract.title)}{marker}"
                )
        else:
            task = load_task_status(journal, task_id)
            if placement.is_sidecar and any(
                record["record_type"] == "acceptance" for record in task.records
            ):
                checked_placement = _placement("status", stderr, require_host=True)
                if checked_placement is None:
                    return 1
                placement = checked_placement
            # Proposal 035's disposition: with --base the command lists the
            # task's records the working tree holds that the named ref does
            # not — resolved in the journal's own repository, so a ref that
            # cannot be answered refuses before anything of the view prints.
            absent = (
                records_absent_from_ref(journal, task, base)
                if base is not None
                else None
            )
            print_task_detail(placement.host_root, task, journal)
            if absent is not None:
                if absent:
                    print(escape_for_display(f"Records absent from {base}:"))
                    for record in absent:
                        print(
                            escape_for_display(
                                f"- {record['id']} {record['record_type']}"
                            )
                        )
                else:
                    print(escape_for_display(f"Records absent from {base}: (none)"))
            print_overdue_steps(
                steps.open_steps(
                    task.task_id,
                    task.records,
                    events_by_task.get(task.task_id, ()),
                    now=now,
                )
            )
    except (OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    return 0


def _run_prune(args: argparse.Namespace, stderr: TextIO) -> int:
    placement = _placement("prune", stderr, require_host=True)
    if placement is None:
        return 1
    if placement.is_sidecar and args.delete:
        print(
            "prune: --delete is refused in a sidecar because the host worktree "
            "and repository must remain read-only",
            file=stderr,
        )
        return 1
    try:
        report = report_branches(placement.host_root, placement.journal_root, args.base)
        worktrees = report_worktrees(placement.host_root, placement.journal_root)
        print("Branches:")
        for item in report:
            label = "eligible" if item.eligible else "skipped"
            print(f"{label}: {item.branch} ({item.reason})")
        print("Worktrees:")
        for worktree in worktrees:
            label = "eligible" if worktree.eligible else "skipped"
            branch = (
                f"branch {worktree.branch}; " if worktree.branch is not None else ""
            )
            print(f"{label}: {worktree.path} ({branch}{worktree.reason})")
        refused = False
        if args.delete:
            for removal in delete_worktrees(placement.host_root, worktrees):
                if removal.removed:
                    print(f"removed worktree: {removal.path}")
                    continue
                refused = True
                print(
                    f"refused worktree: {removal.path} ({removal.detail})",
                    file=stderr,
                )
            for deletion in delete_branches(placement.host_root, report):
                if deletion.deleted:
                    print(f"deleted: {deletion.branch}")
                    continue
                # Asked to delete and did not: say so, and do not report
                # success. git refusing is a disagreement worth surfacing.
                refused = True
                print(
                    f"refused: {deletion.branch} ({deletion.detail})",
                    file=stderr,
                )
    except PruneError as error:
        print(f"prune: {error}", file=stderr)
        return 1
    return 1 if refused else 0


def _run_migrate_journal(
    source: Path, target: Path, stderr: TextIO, *, lenient: bool = False
) -> int:
    report: list[str] = []
    try:
        summaries = migrate_journal(source, target, lenient=lenient, report=report)
    except (JournalMigrationError, OSError, ValueError) as error:
        print(error, file=stderr)
        return 1
    for note in report:
        print(f"note: {note}", file=stderr)
    for summary in summaries:
        print(summary)
    if lenient:
        print(f"Migrated {len(summaries)} task(s); {len(report)} lenient note(s).")
    else:
        print(f"Migrated {len(summaries)} task(s).")
    return 0


class _LeakScanGitError(Exception):
    """A git invocation for leak-scan failed or produced undecodable output."""


def _leak_scan_git(cwd: Path, arguments: list[str]) -> str:
    """Run git under *cwd* and return UTF-8 stdout, or raise a clean error.

    Bytes are captured and decoded explicitly so that a non-zero exit, a
    missing git, or non-UTF-8 output (git permits non-UTF-8 paths and
    content) all surface as :class:`_LeakScanGitError` — never a traceback,
    so the CLI can always return the contract's clean 0/1.
    """

    try:
        result = subprocess.run(
            ["git", *arguments], cwd=cwd, capture_output=True, check=True
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise _LeakScanGitError(str(error)) from error
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _LeakScanGitError(f"non-UTF-8 git output: {error}") from error


def _leak_scan_acknowledgements(
    journal_root: Path, commit: str, task_id: str | None
) -> list[dict[str, object]]:
    """The journal's ``acknowledgement`` records bound to *commit*.

    Read where the gate reads records — every task, or the one ``--task``
    names — through the status loaders the other commands use, so a task
    whose records cannot be projected is a task whose records cannot be
    read: the caller reports why and acknowledges nothing.
    """

    tasks = (
        [load_task_status(journal_root, task_id)]
        if task_id is not None
        else list_task_statuses(journal_root)
    )
    return [
        record
        for task in tasks
        for record in task.records
        if record.get("record_type") == "acknowledgement"
        and record.get("commit") == commit
    ]


def _run_leak_scan(args: argparse.Namespace, stderr: TextIO) -> int:
    # leak-scan is provider-neutral and works in any git repository. Bind to
    # the CURRENT checkout: find_git_root gives this repo's top level, and
    # discovering the project with stop_at=git_root keeps a nested plain git
    # repo from binding to an ancestor AgentMarshal repo's project.json. An
    # AgentMarshal project supplies configured private markers (from the base
    # tree); without one the built-in secret signatures still run, so any CI
    # can call it on a plain checkout. Merge-base resolution goes through
    # _leak_scan_git and the diff through leak_scan_diff — failures surface as
    # a clean 1, and non-UTF-8 content is a named per-file degradation, not a
    # refusal; either way, never a traceback.
    # find_git_root refuses through AgentMarshalProjectError when git is missing
    # or reports an undecodable path (CR-053); either way there is no repository
    # to scan from here.
    try:
        git_root = find_git_root(Path.cwd())
    except AgentMarshalProjectError:
        git_root = None
    if git_root is None:
        print(
            "agentmarshal leak-scan must be run inside a git repository",
            file=stderr,
        )
        return 1
    project_root = find_project_root(Path.cwd(), stop_at=git_root)
    sidecar_config: Path | None = None
    placement: Placement | None = None
    if project_root is None:
        scan_root = git_root
    else:
        try:
            placement = resolve_placement(project_root, require_host=True)
        except PlacementError as error:
            print(error, file=stderr)
            return 1
        scan_root = placement.host_root
        # The content to scan comes from the host; the configured markers come
        # from the trusted side, which in a sidecar is the operator's own
        # repository. Reading them from the host disabled the operator's guard
        # silently whenever the host had no project.json of its own.
        sidecar_config = placement.project_root if placement.is_sidecar else None
    # Resolve the merge base explicitly: markers are read from that trusted
    # tree (as the gate does) so a candidate cannot weaken its own scan, and
    # only the candidate's own additions since the merge base are scanned.
    try:
        merge_base = _leak_scan_git(
            scan_root, ["merge-base", args.base, args.commit]
        ).strip()
    except _LeakScanGitError as error:
        print(
            f"leak-scan: cannot find the merge base of {args.base} and "
            f"{args.commit}: {error}",
            file=stderr,
        )
        return 1
    try:
        # Content comes from the host; the configured markers come from the
        # trusted side, which in a sidecar is the operator's own repository.
        # Reading them from the host silently disabled the operator's guard
        # while the scan still reported success.
        markers = (
            markers_from_config(sidecar_config)
            if sidecar_config is not None
            else markers_from_tree(scan_root, merge_base)
        )
    except (GateError, ValueError, CaptureError) as error:
        print(f"leak-scan: cannot read project config: {error}", file=stderr)
        return 1
    # The pinned diff is the gate's, fetched and decoded per file by the same
    # helper, so the command cannot degrade where the gate does not: a file
    # whose bytes are not UTF-8 is named rather than sinking the whole scan.
    try:
        diff_text, undecodable = leak_scan_diff(scan_root, merge_base, args.commit)
    except GateError as error:
        print(f"leak-scan: git diff failed: {error}", file=stderr)
        return 1
    # The same reasoning the gate applies: the declaration a marker may match
    # is the project file the markers were read from. Here that file is the
    # sidecar's whenever one supplied the markers, and the diff is the host's,
    # so no path in it is that file and nothing is suppressed.
    hits = scan_diff_for_leaks(
        diff_text,
        markers,
        config_path="" if sidecar_config is not None else PROJECT_CONFIG_RELPATH,
    )
    # ADR-0021 decisions 2 and 3: an acknowledgement bound to the
    # candidate's commit, the file exactly as the scan prints it and the
    # hit's identification marks the hit — acknowledged, by whom and why —
    # and an acknowledged hit no longer fails the run, while one nobody
    # acknowledged still does. The records are read where the gate reads
    # them — the journal the placement resolves, every task of it or the
    # one --task names. A repository carrying no journal has no records to
    # find and reads nothing; a read that fails acknowledges nothing and
    # says why — the failure direction is the exit 1 today already gave.
    acknowledgements: list[dict[str, object]] = []
    if placement is not None:
        try:
            resolved_commit = _leak_scan_git(
                scan_root,
                ["rev-parse", "--verify", f"{args.commit}^{{commit}}"],
            ).strip()
            if len(resolved_commit) != 40:
                raise _LeakScanGitError(f"{args.commit} did not resolve to a commit")
            acknowledgements = _leak_scan_acknowledgements(
                placement.journal_root, resolved_commit, args.task
            )
        except (_LeakScanGitError, OSError, ValueError) as error:
            # The message can carry a path or a record field the tool did
            # not write — escaped the way every transcript value is.
            print(
                "leak-scan: cannot read acknowledgements: "
                + escape_for_display(str(error)),
                file=stderr,
            )
    elif args.task is not None:
        print(
            "leak-scan: cannot read acknowledgements: this repository "
            "has no AgentMarshal journal",
            file=stderr,
        )
    # Files that did not decode are a caveat about the scan, printed beside
    # the best-effort note rather than as hits: their bytes were still
    # searched, and an ordinary binary file must not fail the run on its own.
    if undecodable:
        print(
            "leak-scan: could not decode as UTF-8 "
            "(added bytes still searched): "
            + render_undecodable_files(undecodable, markers, limit=None),
            file=stderr,
        )
    if hits:
        # The mark is capture.py's, the one the gate's advisory line
        # builds its marks with — one implementation, so the two
        # surfaces cannot drift on wording, masking or escaping.
        marks = [_acknowledgement_mark(hit, acknowledgements, markers) for hit in hits]
        print(
            "leak-scan: possible leaks in added content "
            "(file: what matched): " + render_leak_hits(hits, limit=None, marks=marks)
        )
        print(
            "(best-effort: a hit is not proof of a leak and a clean run is not "
            "proof of safety — see ADR-0005)",
            file=stderr,
        )
        return 0 if all(mark is not None for mark in marks) else 1
    print("leak-scan: no known leak signatures in added content")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AgentMarshal CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _run_init(args.host, sys.stderr)
    if args.command == "doctor":
        return _run_doctor()
    if args.command == "validate":
        return _run_validate(sys.stderr)
    if args.command == "open":
        return _run_open(args, sys.stderr)
    if args.command == "brief":
        return _run_brief(args.task, sys.stderr)
    if args.command == "status":
        return _run_status(args.task_id, args.base, sys.stderr)
    if args.command == "submit-review":
        return _run_submit_review(args, sys.stderr)
    if args.command == "accept":
        return _run_accept(args, sys.stderr)
    if args.command == "review":
        return _run_review(args, sys.stderr)
    if args.command == "gate":
        return _run_gate(args, sys.stderr)
    if args.command == "complete":
        return _run_complete(args, sys.stderr)
    if args.command == "abandon":
        return _run_abandon(args, sys.stderr)
    if args.command == "reopen":
        return _run_reopen(args, sys.stderr)
    if args.command == "amend":
        return _run_amend(args, sys.stderr)
    if args.command == "record-session":
        return _run_record_session(args, sys.stderr)
    if args.command == "finding":
        return _run_finding(args, sys.stderr)
    if args.command == "report":
        return _run_report(args.task, sys.stderr, findings=args.findings)
    if args.command == "prune":
        return _run_prune(args, sys.stderr)
    if args.command == "migrate-journal":
        return _run_migrate_journal(
            args.source, args.target, sys.stderr, lenient=args.lenient
        )
    if args.command == "leak-scan":
        return _run_leak_scan(args, sys.stderr)
    if args.command == "acknowledge":
        return acknowledge.run(args, sys.stderr)
    if args.command == "outbox":
        return outbox.run(args, sys.stderr)
    if args.command == "step":
        return steps.run(args, sys.stderr)
    if args.command == "stage":
        return stages.run(args, sys.stderr)
    if args.command == "extension":
        return extension_trust.run(args, sys.stderr)
    if args.command == "agree":
        return agree.run(args, sys.stderr)
    if args.command == "record-check":
        return record_check.run(args, sys.stderr)
    if args.command == "record-ext":
        return record_ext.run(args, sys.stderr)

    parser.error(f"unknown command: {args.command}")
