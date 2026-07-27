"""Command-line interface for AgentMarshal."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO, cast

from agentmarshal import __version__
from agentmarshal.doctor import run_doctor
from agentmarshal.journal.complete import (
    LifecycleError,
    abandon_task,
    complete_task,
)
from agentmarshal.journal.gate import GateError, run_gate
from agentmarshal.journal.gate_context import derive_gate_context
from agentmarshal.journal.open_task import TaskOpenError, open_task
from agentmarshal.journal.report import ReportError, build_report, format_report
from agentmarshal.journal.review import ReviewLaunchError, launch_review
from agentmarshal.journal.session import SessionRecordError, record_session
from agentmarshal.journal.status import (
    TaskStatus,
    TaskStatusError,
    list_task_statuses,
    load_task_status,
)
from agentmarshal.journal.submit_review import ReviewSubmitError, submit_review
from agentmarshal.journal.validate import validate_journal
from agentmarshal.migrate import JournalMigrationError, migrate_journal
from agentmarshal.project import (
    AgentMarshalProjectError,
    AlreadyInitializedError,
    find_project_root,
    initialize_project,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentmarshal")
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="initialize AgentMarshal project metadata")
    subparsers.add_parser("doctor", help="check AgentMarshal project health")
    subparsers.add_parser("validate", help="validate the whole journal for integrity")
    open_parser = subparsers.add_parser("open", help="open a journal task")
    open_parser.add_argument("--title", required=True, help="task title")
    open_parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="path included in the task scope (repeatable)",
    )
    status_parser = subparsers.add_parser("status", help="show journal task status")
    status_parser.add_argument("task_id", nargs="?", help="task identifier")
    review_parser = subparsers.add_parser(
        "submit-review", help="record a task review verdict"
    )
    review_parser.add_argument("--task", required=True, help="task identifier")
    review_parser.add_argument("--commit", required=True, help="reviewed commit SHA")
    review_parser.add_argument("--verdict", required=True, help="review verdict")
    review_parser.add_argument(
        "--finding", action="append", default=[], help="finding id (repeatable)"
    )
    review_parser.add_argument("--role", required=True, help="reviewer role")
    review_parser.add_argument("--vendor", required=True, help="reviewer vendor")
    review_parser.add_argument("--model", required=True, help="reviewer model")
    review_parser.add_argument("--email", required=True, help="reviewer email")
    launch_parser = subparsers.add_parser(
        "review", help="run and record a read-only task review"
    )
    launch_parser.add_argument("--task", required=True, help="task identifier")
    launch_parser.add_argument("--commit", required=True, help="reviewed commit SHA")
    launch_parser.add_argument("--base", required=True, help="comparison base ref")
    launch_parser.add_argument("--role", required=True, help="reviewer role")
    launch_parser.add_argument("--vendor", required=True, help="reviewer vendor")
    launch_parser.add_argument("--model", required=True, help="reviewer model")
    launch_parser.add_argument("--email", required=True, help="reviewer email")
    gate_parser = subparsers.add_parser(
        "gate", help="verify a merge candidate against the journal"
    )
    gate_parser.add_argument(
        "--task",
        default=None,
        help="task identifier (default: derived from the current branch name)",
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
    complete_parser.add_argument("--commit", required=True, help="candidate head SHA")
    complete_parser.add_argument("--base", required=True, help="merge target ref")
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
    session_parser = subparsers.add_parser(
        "record-session", help="record attributed task work"
    )
    session_parser.add_argument("--task", required=True, help="task identifier")
    session_parser.add_argument("--role", required=True, help="worker role")
    session_parser.add_argument("--actor", required=True, help="worker identity")
    session_parser.add_argument(
        "--activity", required=True, help="implementation, review, or other"
    )
    session_parser.add_argument("--outcome", required=True, help="work outcome")
    session_parser.add_argument("--input-tokens", type=int, default=0)
    session_parser.add_argument("--output-tokens", type=int, default=0)
    session_parser.add_argument("--cache-tokens", type=int, default=0)
    report_parser = subparsers.add_parser(
        "report", help="summarize task delegation economics"
    )
    report_parser.add_argument("--task", help="task identifier")
    migrate_parser = subparsers.add_parser(
        "migrate-journal", help="convert a v1 journal into a new v2 journal"
    )
    migrate_parser.add_argument("--source", required=True, type=Path)
    migrate_parser.add_argument("--target", required=True, type=Path)
    return parser


def _run_init(stderr: TextIO) -> int:
    try:
        project_root = initialize_project(Path.cwd())
    except AlreadyInitializedError as error:
        print(error, file=stderr)
        return 1
    except AgentMarshalProjectError as error:
        print(error, file=stderr)
        return 1

    print(f"Initialized AgentMarshal project at {project_root}")
    return 0


def _run_doctor() -> int:
    results = run_doctor()
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"{status}: {result.name} — {result.detail}")
    failures = sum(not result.ok for result in results)
    if failures:
        print(f"Summary: {failures} check(s) failed")
        return 1
    print(f"Summary: all {len(results)} checks passed")
    return 0


def _run_open(title: str, scope: list[str], stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal open must be run inside an initialized project", file=stderr
        )
        return 1
    try:
        opened_task = open_task(project_root, title, scope)
    except TaskOpenError as error:
        print(error, file=stderr)
        return 1
    print(opened_task.contract_path)
    print(opened_task.record_path)
    return 0


def _print_task_detail(task: TaskStatus) -> None:
    print(f"ID: {task.task_id}")
    print(f"Status: {task.state}")
    print(f"Title: {task.contract.title}")
    print("Scope:")
    if task.contract.scope:
        for path in task.contract.scope:
            print(f"- {path}")
    else:
        print("- (none)")
    print("Records:")
    for record in task.records:
        if record["record_type"] == "review":
            findings = cast(list[object], record["findings"])
            print(
                f"- {record['id']} review {record['created_at']} "
                f"reviewed_commit={str(record['reviewed_commit'])[:7]} "
                f"verdict={record['verdict']} findings={len(findings)}"
            )
        elif record["record_type"] == "completed":
            print(
                f"- {record['id']} completed {record['created_at']} "
                f"completed_commit={str(record['completed_commit'])[:7]}"
            )
        elif record["record_type"] == "abandoned":
            print(
                f"- {record['id']} abandoned {record['created_at']} "
                f"reason={record['reason']}"
            )
        else:
            print(f"- {record['id']} {record['record_type']} {record['created_at']}")


def _run_submit_review(args: argparse.Namespace, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal submit-review must be run inside an initialized project",
            file=stderr,
        )
        return 1
    try:
        submitted = submit_review(
            project_root / ".agentmarshal" / "journal",
            args.task,
            args.commit,
            args.verdict,
            args.role,
            args.vendor,
            args.model,
            args.email,
            args.finding,
        )
    except ReviewSubmitError as error:
        print(error, file=stderr)
        return 1
    print(submitted.record_path)
    return 0


def _run_review(args: argparse.Namespace, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal review must be run inside an initialized project",
            file=stderr,
        )
        return 1
    try:
        submitted = launch_review(
            project_root,
            args.task,
            args.commit,
            args.base,
            args.role,
            args.vendor,
            args.model,
            args.email,
        )
    except ReviewLaunchError as error:
        print(error, file=stderr)
        return 1
    print(submitted.record_path)
    return 0


def _run_validate(stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal validate must be run inside an initialized project",
            file=stderr,
        )
        return 1
    report = validate_journal(project_root)
    for line in report.lines:
        print(line)
    if not report.passed:
        print("validate: journal invalid", file=stderr)
        return 1
    print("validate: passed")
    return 0


def _run_gate(args: argparse.Namespace, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal gate must be run inside an initialized project", file=stderr
        )
        return 1
    pipeline_sha = args.pipeline_sha or os.environ.get("AGENTMARSHAL_PIPELINE_OK_SHA")
    try:
        context = derive_gate_context(project_root, args.task, args.commit, args.base)
        report = run_gate(
            project_root,
            context.task,
            context.commit,
            context.base,
            pipeline_sha,
            attestation=args.attestation,
        )
    except GateError as error:
        print(error, file=stderr)
        return 1
    for line in report.lines:
        print(line)
    if not report.passed:
        print("gate: refused", file=stderr)
        return 1
    print("gate: passed")
    return 0


def _run_complete(args: argparse.Namespace, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal complete must be run inside an initialized project",
            file=stderr,
        )
        return 1
    pipeline_sha = args.pipeline_sha or os.environ.get("AGENTMARSHAL_PIPELINE_OK_SHA")
    try:
        result = complete_task(
            project_root, args.task, args.commit, args.base, pipeline_sha
        )
    except LifecycleError as error:
        print(error, file=stderr)
        return 1
    for line in result.report.lines:
        print(line)
    if result.record_path is None:
        print("complete: gate refused; task not completed", file=stderr)
        return 1
    print(result.record_path)
    print("completed")
    return 0


def _run_abandon(args: argparse.Namespace, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal abandon must be run inside an initialized project",
            file=stderr,
        )
        return 1
    try:
        record_path = abandon_task(project_root, args.task, args.reason)
    except LifecycleError as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print("abandoned")
    return 0


def _run_record_session(args: argparse.Namespace, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal record-session must be run inside an initialized project",
            file=stderr,
        )
        return 1
    try:
        record_path = record_session(
            project_root / ".agentmarshal" / "journal",
            args.task,
            args.role,
            args.actor,
            args.activity,
            args.outcome,
            args.input_tokens,
            args.output_tokens,
            args.cache_tokens,
        )
    except SessionRecordError as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    return 0


def _run_report(task_id: str | None, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal report must be run inside an initialized project",
            file=stderr,
        )
        return 1
    try:
        report = build_report(project_root / ".agentmarshal" / "journal", task_id)
    except ReportError as error:
        print(error, file=stderr)
        return 1
    for line in format_report(report, include_summary=task_id is None):
        print(line)
    return 0


def _run_status(task_id: str | None, stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal status must be run inside an initialized project", file=stderr
        )
        return 1
    journal = project_root / ".agentmarshal" / "journal"
    try:
        if task_id is None:
            tasks = list_task_statuses(journal)
            if not tasks:
                print("No tasks.")
                return 0
            for task in tasks:
                print(f"{task.task_id}\t{task.state}\t{task.contract.title}")
        else:
            _print_task_detail(load_task_status(journal, task_id))
    except (OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    return 0


def _run_migrate_journal(source: Path, target: Path, stderr: TextIO) -> int:
    try:
        summaries = migrate_journal(source, target)
    except (JournalMigrationError, OSError, ValueError) as error:
        print(error, file=stderr)
        return 1
    for summary in summaries:
        print(summary)
    print(f"Migrated {len(summaries)} task(s).")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AgentMarshal CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _run_init(sys.stderr)
    if args.command == "doctor":
        return _run_doctor()
    if args.command == "validate":
        return _run_validate(sys.stderr)
    if args.command == "open":
        return _run_open(args.title, args.scope, sys.stderr)
    if args.command == "status":
        return _run_status(args.task_id, sys.stderr)
    if args.command == "submit-review":
        return _run_submit_review(args, sys.stderr)
    if args.command == "review":
        return _run_review(args, sys.stderr)
    if args.command == "gate":
        return _run_gate(args, sys.stderr)
    if args.command == "complete":
        return _run_complete(args, sys.stderr)
    if args.command == "abandon":
        return _run_abandon(args, sys.stderr)
    if args.command == "record-session":
        return _run_record_session(args, sys.stderr)
    if args.command == "report":
        return _run_report(args.task, sys.stderr)
    if args.command == "migrate-journal":
        return _run_migrate_journal(args.source, args.target, sys.stderr)

    parser.error(f"unknown command: {args.command}")
