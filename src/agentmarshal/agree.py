"""The ``agree`` command: an actor's agreement with a task's contract.

ADR-0018 decision 2 and ADR-0022 section 3: a declared actor states
agreement with the contract at a stated hash — any declared actor may,
there are no roles — and a recorder that is not a declared actor is still
accepted. ``agree`` writes one ``agreement`` record whose ``contract`` is
the ``contract_sha256`` of the task's ``contract.md`` as it stands, the
one function ``open`` and ``amend`` pin with, and prints the hash and the
recorder. ``--contract`` binds the agreement to the text the actor read:
the command writes only when the hash given equals the current one.

A drifted contract is refused until ``amend`` records the edit —
agreeing with a text no record pins is agreeing with something the
journal cannot name. A task opened before contract hashes existed has no
pin; agreement then pins the current text and the refusal does not apply.
Every refusal writes nothing and names its reason.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.journal.actors import SOURCE_ACTORS_TABLE, resolve_recorded_by
from agentmarshal.journal.contracts import JournalContractError, contract_sha256
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.placement import Placement, PlacementError, resolve_placement
from agentmarshal.journal.records import (
    JournalRecordError,
    _project_root_for,
    create_agreement_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from agentmarshal.project import (
    find_project_root,
    project_file_path,
    read_project_file,
)

#: The shape the record family's `contract` field takes — and the only
#: shape `--contract` accepts: anything else is a mistyped hash, named
#: with the field that failed.
_CONTRACT_ARGUMENT = re.compile(r"[0-9a-f]{64}$")


class AgreeError(Exception):
    """Raised when agreement cannot be recorded, the message naming why."""


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``agree`` command to *subparsers*."""

    agree_parser = subparsers.add_parser(
        "agree", help="record agreement with a task's contract at its current hash"
    )
    agree_parser.add_argument("--task", required=True, help="task identifier")
    agree_parser.add_argument(
        "--contract",
        help="the hash of the contract text read — the command writes only "
        "when it equals the contract's current hash",
    )


def _placement(stderr: TextIO) -> Placement | None:
    """Resolve the journal placement, or print why it cannot be had."""

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal agree must be run inside an initialized project",
            file=stderr,
        )
        return None
    try:
        return resolve_placement(project_root)
    except PlacementError as error:
        # The message can carry a value the tool did not write — a host
        # path from project.json, git's own error text — so it is escaped
        # the way a transcript line is, as cli.py's placement does.
        print(escape_for_display(str(error)), file=stderr)
        return None


def _latest_pin(records: tuple[dict[str, object], ...]) -> str | None:
    """The contract hash of the task's latest pin, or ``None``.

    The pin is the `contract` carried by the latest `opened` or
    `amendment` record that carries one — the same scan
    `status_view._contract_drift_line` makes, restated here over the
    records `load_task_for_record` already returned: the view module's
    copy lives behind the line it renders, and growing a public function
    there to serve a writer is a wider change than the handful of lines
    this restates.
    """

    pinned: str | None = None
    for record in records:
        if record["record_type"] in ("opened", "amendment"):
            contract = record.get("contract")
            if isinstance(contract, str):
                pinned = contract
    return pinned


def _declared_actor(project_root: Path, recorder: str, source: str) -> bool:
    """Whether *recorder* names an actor the project file declares.

    A `project-actor` resolution implies it — the id came out of the
    table. An override or a git identity can still *name* a declared
    actor, so declared-ness is tested on the id against the project
    file's `actors` keys — the table `_actor_git_identities` reads — not
    on the resolution's source. A project file that cannot be read
    declares nothing; undeclared is a note, never a refusal.
    """

    if source == SOURCE_ACTORS_TABLE:
        return True
    try:
        project = read_project_file(project_file_path(project_root))
    except (OSError, ValueError):
        return False
    actors = project.get("actors")
    return isinstance(actors, dict) and recorder in actors


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Record the invoking actor's agreement with a task's contract."""

    given = args.contract
    if given is not None and _CONTRACT_ARGUMENT.fullmatch(given) is None:
        print(
            "agree: --contract must be exactly 64 lowercase hex characters",
            file=stderr,
        )
        return 1
    placement = _placement(stderr)
    if placement is None:
        return 1
    journal_root = placement.journal_root
    try:
        task = load_task_for_record(journal_root, args.task, "agreement")
        # The hash is the journal repository's contract as it stands — in
        # a sidecar, the sidecar's copy, the one amend pins (ADR-0018
        # decision 1). A contract that does not parse was refused by the
        # load above, and bytes that do not decode are refused by the
        # hash itself.
        contract_path = journal_root / "tasks" / args.task / "contract.md"
        current = contract_sha256(contract_path.read_bytes(), str(contract_path))
        pinned = _latest_pin(task.records)
        # A `--contract` that is not the current hash names what the actor
        # read against what stands — the refusal owes it both, so it is
        # decided before drift, whose refusal names the pin instead.
        if given is not None and given != current:
            raise AgreeError(
                f"--contract {given} does not equal the contract's "
                f"current hash {current}"
            )
        if pinned is not None and current != pinned:
            raise AgreeError(
                f"the contract drifted from its pin {pinned[:7]} "
                f"(now {current[:7]}); record the edit with amend first"
            )
        # The agreement requires its recorder, so the resolution the
        # record rules would refuse on is decided here, before anything
        # is written — on the same root `write_record` resolves it from.
        recorder_root = _project_root_for(journal_root)
        resolved = resolve_recorded_by(recorder_root)
        if resolved is None:
            raise AgreeError(
                "no recorder identity could be resolved; set "
                "AGENTMARSHAL_ACTOR or configure git user.email"
            )
        recorder, source = resolved
        record = create_agreement_record(args.task, __version__, current)
        record_path = write_record(journal_root, args.task, record)
    except (AgreeError, JournalContractError) as error:
        print(f"agree: {error}", file=stderr)
        return 1
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print(f"contract {current}")
    print(f"recorded by {escape_for_display(recorder)}")
    if not _declared_actor(recorder_root, recorder, source):
        print(
            f"note: {escape_for_display(recorder)} is not a declared actor",
            file=stderr,
        )
    return 0
