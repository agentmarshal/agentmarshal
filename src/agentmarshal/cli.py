"""Command-line interface for AgentMarshal."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.project import (
    AgentMarshalProjectError,
    AlreadyInitializedError,
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


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AgentMarshal CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _run_init(sys.stderr)

    parser.error(f"unknown command: {args.command}")
