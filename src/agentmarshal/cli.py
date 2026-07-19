"""Command-line interface for AgentMarshal."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.journal.open_task import TaskOpenError, open_task
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
    open_parser = subparsers.add_parser("open", help="open a journal task")
    open_parser.add_argument("--title", required=True, help="task title")
    open_parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="path included in the task scope (repeatable)",
    )
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


def _run_open(title: str, scope: list[str], stderr: TextIO) -> int:
    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print("agentmarshal open must be run inside an initialized project", file=stderr)
        return 1
    try:
        opened_task = open_task(project_root, title, scope)
    except TaskOpenError as error:
        print(error, file=stderr)
        return 1
    print(opened_task.contract_path)
    print(opened_task.record_path)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AgentMarshal CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _run_init(sys.stderr)
    if args.command == "open":
        return _run_open(args.title, args.scope, sys.stderr)

    parser.error(f"unknown command: {args.command}")
