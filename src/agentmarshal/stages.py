"""The ``stage`` command group: run the shared extensions' declared stages.

ADR-0013 section A — decisions 1, 2, 4, 5, 6 and 7 — and decision 14:
an extension's one obligation is to be invoked at its declared stage;
``pre-gate`` runs the ``pre-gate-warn`` and ``pre-gate-stop`` modes and
``post-gate`` runs ``post-gate``; an extension is a separate step before
the gate and the gate reads none of its output; manifests and the code of
shared extensions come from the base commit; every extension gets a
result line and its output a frame that cannot read as a gate line. On a
workstation a stage runs only under a local grant matching the hash of
the base-materialized directory (CR-209's ``trust.toml``); in CI no grant
is needed. Each result is appended to the process log as an
``extension-event`` (ADR-0022 section 7); nothing is written to the
journal. A ``pre-gate-stop`` stage that failed, did not finish or did not
run pauses the process before the gate — the command exits 3 — while a
``pre-gate-warn`` stage's failure is a loud warning and a ``post-gate``
stage's only a notification.

The invocation protocol — what the command receives and what its exit
status means — is the coordinator's decision recorded in the change's
design: the stage's working directory is a fresh temporary snapshot of
the candidate commit; the environment carries the five ``AGENTMARSHAL_*``
protocol variables, a minimal ``PATH`` and only the variables the
manifest's ``isolation.env`` names; the command runs as ``[<the core's
Python interpreter>, <the path under bin/>]``, never through a shell and
never through ``PATH`` lookup; a time limit of the declared
``timeout_seconds`` capped by the core's limit bounds it, the process
group killed on a breach; exit status 0 means checked, any other failed.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, TextIO

from agentmarshal.extension_trust import (
    ExtensionTrustError,
    Grant,
    _changed_after_approval,
    _hash_directory,
    _read_grants,
)
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    ExtensionManifest,
    ExtensionManifestError,
    ExtensionPhase,
    ExtensionStage,
)
from agentmarshal.journal.gate import (
    GateError,
    _manifest_from_tree,
    _resolve_commit,
    _run_git,
    _run_git_bytes,
    _run_git_lossy,
    _tree_entry,
)
from agentmarshal.journal.placement import (
    Placement,
    PlacementError,
    resolve_placement,
)
from agentmarshal.journal.records import JournalRecordError, validate_task_id
from agentmarshal.journal.review import ReviewLaunchError, _extract_snapshot
from agentmarshal.localstate import LocalState, LocalStateError, local_state
from agentmarshal.process_log import (
    ProcessLogError,
    ProcessLogWriter,
    open_writer,
    write_event,
)
from agentmarshal.project import find_project_root

#: The core's time limit for one stage; a manifest may declare less
#: (ADR-0013 decision 8's floor: the timeout no higher than the core's).
STAGE_TIME_LIMIT_SECONDS = 600

#: How long the second ``communicate`` waits after the group is killed:
#: a detached grandchild holding the pipes open must not hang the run,
#: so the drain is bounded too and the pipes are closed past it.
_DRAIN_TIMEOUT_SECONDS = 5

#: The minimal ``PATH`` every stage's environment starts with: two
#: fixed system directories and no empty element — an empty element
#: would name the stage's working directory, the candidate snapshot.
_MINIMAL_PATH = "/usr/bin:/bin"

_EXTENSIONS_RELPATH = ".agentmarshal/extensions"

#: The manifest modes each ``--phase`` value invokes (ADR-0013 decisions
#: 2 and 4): ``pre-gate`` covers both pre-gate modes, ``post-gate`` the
#: notification mode.
_PHASE_MODES: dict[str, tuple[ExtensionPhase, ...]] = {
    "pre-gate": ("pre-gate-warn", "pre-gate-stop"),
    "post-gate": ("post-gate",),
}

_StageDecision = Literal["checked", "failed", "did-not-finish", "not-run"]


class StageError(Exception):
    """Raised when a stage's own machinery cannot evaluate it."""


@dataclass(frozen=True)
class _Prepared:
    """One extension's run prerequisites: its directory, or why it may not run."""

    directory: Path | None
    reason: str | None
    # The reason the ``extension-event`` records where it may carry
    # more than the result line does — the result line's spellings are
    # the specification's own.
    event_reason: str | None = None


@dataclass(frozen=True)
class _Outcome:
    """One stage's result: the decision word, its detail and captured output."""

    decision: _StageDecision
    reason: str
    output: bytes
    event_reason: str | None = None


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``stage`` group and its subcommand to *subparsers*."""

    stage_parser = subparsers.add_parser(
        "stage", help="run the shared extensions' declared stages"
    )
    stage_commands = stage_parser.add_subparsers(dest="stage_command", required=True)
    run_parser = stage_commands.add_parser(
        "run", help="run every shared extension stage matching the phase"
    )
    run_parser.add_argument(
        "--phase",
        required=True,
        choices=("pre-gate", "post-gate"),
        help="which stage to invoke: pre-gate runs the pre-gate-warn and "
        "pre-gate-stop modes, post-gate the post-gate mode",
    )
    run_parser.add_argument("--task", required=True, help="task identifier")
    run_parser.add_argument("--commit", required=True, help="candidate head revision")
    run_parser.add_argument(
        "--base", required=True, help="merge target ref the candidate is compared to"
    )


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Dispatch the parsed ``stage`` subcommand."""

    if args.stage_command == "run":
        return _run_stages(args, stderr)
    print(f"stage: unknown command {args.stage_command}", file=stderr)
    return 1


def _resolve(stderr: TextIO) -> tuple[Placement, LocalState] | None:
    """Resolve the journal placement and its local state, or print why not.

    The same resolution ``extension trust`` performs: local state names the
    git common directory of the repository that holds the journal, so the
    grants file and the log land in that repository's own local state.
    """

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal stage run must be run inside an initialized project; "
            "run agentmarshal init in the repository first",
            file=stderr,
        )
        return None
    try:
        placement = resolve_placement(project_root)
        return placement, local_state(placement)
    except (PlacementError, LocalStateError) as error:
        print(escape_for_display(str(error)), file=stderr)
        return None


def _base_manifests(
    project_root: Path, merge_base: str
) -> dict[str, ExtensionManifest]:
    """Each directory-form shared extension's manifest at the base tree.

    Discovery is the tree counterpart of the working-tree rule: a symlink
    at ``.agentmarshal``, at ``extensions/`` or at an extension's ``<name>``
    is refused as a link before existence is weighed, an ``extensions/``
    that is missing or not a tree is simply no directory-form extensions,
    and a ``<name>.toml`` entry is the file form, which declares no
    directory and so no stage. Each surviving name is read with the gate's
    own base-tree reader, so its file-and-directory-form, link and schema
    refusals apply unchanged rather than being restated here.
    """

    agentmarshal_entry = _tree_entry(project_root, merge_base, ".agentmarshal")
    if agentmarshal_entry is not None and agentmarshal_entry[0] == "120000":
        raise ExtensionManifestError(
            f"refusing to read extensions through a symlink: {merge_base}:.agentmarshal"
        )
    extensions_entry = _tree_entry(project_root, merge_base, _EXTENSIONS_RELPATH)
    if extensions_entry is not None and extensions_entry[0] == "120000":
        raise ExtensionManifestError(
            f"refusing to read extensions through a symlink: "
            f"{merge_base}:{_EXTENSIONS_RELPATH}"
        )
    if agentmarshal_entry is None or agentmarshal_entry[1] != "tree":
        return {}
    if extensions_entry is None or extensions_entry[1] != "tree":
        return {}
    listing = _run_git_lossy(
        project_root, ["ls-tree", "-z", merge_base, "--", f"{_EXTENSIONS_RELPATH}/"]
    )
    names: list[str] = []
    for item in listing.split("\0"):
        if not item:
            continue
        meta, _, path = item.partition("\t")
        fields = meta.split(" ")
        mode, kind = fields[0], fields[1]
        if kind == "tree":
            names.append(path.rsplit("/", maxsplit=1)[-1])
        elif mode == "120000":
            raise ExtensionManifestError(
                f"refusing to read extension "
                f"{path.rsplit('/', maxsplit=1)[-1]!r} through a symlink: "
                f"{merge_base}:{path}"
            )
    return {
        name: _manifest_from_tree(project_root, merge_base, name)
        for name in sorted(names)
    }


def _materialize_directory(
    project_root: Path, tree_ref: str, name: str, destination: Path
) -> None:
    """Extract ``.agentmarshal/extensions/<name>/`` at *tree_ref* into *destination*.

    A ``git show`` of each blob the ``ls-tree -r`` listing names, written
    byte for byte: ``git archive`` would honour ``export-ignore`` and
    ``export-subst``, and a grant is over the tree's contents, so the
    materialization must carry them undoctored. A symbolic-link entry is
    recreated as a link — the run then refuses the directory holding it,
    as the grant hash does — and a gitlink is refused: an object store
    entry that is not a blob cannot be materialized.
    """

    relpath = f"{_EXTENSIONS_RELPATH}/{name}"
    listing = _run_git_lossy(
        project_root,
        ["ls-tree", "-r", "-z", tree_ref, "--", f":(literal){relpath}"],
    )
    for item in listing.split("\0"):
        if not item:
            continue
        meta, _, path = item.partition("\t")
        fields = meta.split(" ")
        mode, kind = fields[0], fields[1]
        relative = PurePosixPath(path).relative_to(relpath)
        target = destination.joinpath(*relative.parts)
        if kind != "blob":
            raise StageError(f"a gitlink inside the extension's directory: {relative}")
        data = _run_git_bytes(project_root, ["show", f"{tree_ref}:{path}"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "120000":
            os.symlink(os.fsdecode(data), target)
        else:
            target.write_bytes(data)


def _symlink_in_directory(directory: Path) -> str | None:
    """The first symbolic link under *directory*, or ``None``.

    The same walk the grant hash performs — sorted, entry by entry, the
    link weighed before its type is — so the refusal names the same
    path here that the grant names on a workstation. A link anywhere in
    the materialized directory can place the command outside what the
    base approved, so the directory itself is refused, in CI as on a
    workstation.
    """

    def walk(root: Path) -> str | None:
        try:
            entries = sorted(root.iterdir())
        except OSError as error:
            raise StageError(
                f"cannot read {root}: {error.strerror or error}"
            ) from error
        for entry in entries:
            if entry.is_symlink():
                return entry.relative_to(directory).as_posix()
            if entry.is_dir():
                found = walk(entry)
                if found is not None:
                    return found
        return None

    return walk(directory)


def _prepare_extension(
    project_root: Path,
    merge_base: str,
    name: str,
    temp_root: Path,
    ci: bool,
    grants: dict[str, Grant],
) -> _Prepared:
    """Materialize one extension's directory and, off CI, check its grant.

    Called once per stage against a fresh *temp_root*: a stage can reach
    its own materialized copy through ``__file__``, so a copy an earlier
    stage could have touched is never reused — decision 14's "before
    each run" is a recomputation on each stage's own materialization.

    A materialized directory holding a symbolic link anywhere is
    refused before the grant is consulted — the refusal the grant hash
    gives on a workstation, applied in CI too, where a linked
    intermediate directory would otherwise put the command outside the
    approved copy. The grant check then runs on the base-materialized
    contents:
    the hash the grant recorded must cover what is about to run, so a
    change landed after the approval — or a directory that cannot be
    hashed at all — is the ``not run`` reason, with the first differing
    file named the way ``extension list`` names it.
    """

    directory = temp_root / "extensions" / name
    try:
        _materialize_directory(project_root, merge_base, name, directory)
    except (GateError, StageError, OSError) as error:
        return _Prepared(None, f"cannot materialize: {escape_for_display(str(error))}")
    try:
        linked = _symlink_in_directory(directory)
    except StageError as error:
        return _Prepared(None, escape_for_display(str(error)))
    if linked is not None:
        return _Prepared(
            None, f"symlink in extension directory: {escape_for_display(linked)}"
        )
    if ci:
        return _Prepared(directory, None)
    try:
        files = _hash_directory(directory)
    except ExtensionTrustError as error:
        return _Prepared(None, escape_for_display(str(error)))
    grant = grants.get(name)
    if grant is None:
        return _Prepared(None, "not granted")
    difference = _changed_after_approval(grant.files, files)
    if difference is not None:
        path, kind = difference
        shown = escape_for_display(path)
        return _Prepared(
            None,
            f"changed after approval: {shown}",
            f"changed after approval: {shown} ({kind})",
        )
    return _Prepared(directory, None)


def _stage_timeout(manifest: ExtensionManifest) -> int:
    """The declared ``timeout_seconds`` capped by the core's limit."""

    if manifest.isolation is None:
        return STAGE_TIME_LIMIT_SECONDS
    return min(manifest.isolation.timeout_seconds, STAGE_TIME_LIMIT_SECONDS)


def _stage_env(
    manifest: ExtensionManifest,
    phase: str,
    task_id: str,
    resolved_commit: str,
    merge_base: str,
    snapshot: Path,
) -> dict[str, str]:
    """The child environment: declared variables, then the protocol's.

    ``PATH`` starts minimal; a manifest naming it — or any other variable
    — receives the caller's value, which is what ``isolation.env`` exists
    to pass. The five protocol variables are written last so a declared
    name colliding with one cannot override the run's own values.
    """

    env: dict[str, str] = {"PATH": _MINIMAL_PATH}
    if manifest.isolation is not None:
        for variable in manifest.isolation.env:
            if variable in os.environ:
                env[variable] = os.environ[variable]
    env.update(
        {
            "AGENTMARSHAL_PHASE": phase,
            "AGENTMARSHAL_TASK": task_id,
            "AGENTMARSHAL_COMMIT": resolved_commit,
            "AGENTMARSHAL_BASE": merge_base,
            "AGENTMARSHAL_SNAPSHOT": str(snapshot),
        }
    )
    return env


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    """Kill the child's whole process group; ``Popen.kill`` where there is none."""

    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except (ProcessLookupError, PermissionError):
            pass
    with suppress(ProcessLookupError):
        process.kill()


def _run_stage(
    project_root: Path,
    resolved_commit: str,
    merge_base: str,
    task_id: str,
    phase: str,
    name: str,
    manifest: ExtensionManifest,
    stage: ExtensionStage,
    prepared: _Prepared,
    snapshot: Path,
) -> _Outcome:
    """Run one stage and report its outcome; never raises for the stage itself."""

    if prepared.reason is not None:
        return _Outcome(
            "not-run", prepared.reason, b"", event_reason=prepared.event_reason
        )
    assert prepared.directory is not None
    command = prepared.directory / stage.command
    if command.is_symlink():
        return _Outcome("not-run", f"command {stage.command} is a symbolic link", b"")
    if not command.is_file():
        return _Outcome("not-run", f"command {stage.command} does not exist", b"")
    try:
        _extract_snapshot(project_root, resolved_commit, snapshot)
    except ReviewLaunchError as error:
        return _Outcome(
            "not-run",
            f"cannot materialize the candidate snapshot: "
            f"{escape_for_display(str(error))}",
            b"",
        )
    argv = [sys.executable, str(command)]
    try:
        process = subprocess.Popen(
            argv,
            cwd=snapshot,
            env=_stage_env(
                manifest, phase, task_id, resolved_commit, merge_base, snapshot
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as error:
        return _Outcome(
            "not-run",
            f"cannot start {stage.command}: "
            f"{escape_for_display(error.strerror or str(error))}",
            b"",
        )
    try:
        output, _ = process.communicate(timeout=_stage_timeout(manifest))
    except subprocess.TimeoutExpired:
        _kill_process_group(process)
        # A detached child can hold the pipes open past the group's
        # death, so the drain is bounded too: a second expiry closes the
        # pipes and the stage is a timeout anyway — the line does not
        # wait on what keeps its end open.
        try:
            output, _ = process.communicate(timeout=_DRAIN_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as still_open:
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    with suppress(OSError):
                        pipe.close()
            process.wait()
            output = still_open.output or b""
        return _Outcome("did-not-finish", "timeout", output)
    if process.returncode == 0:
        return _Outcome("checked", "", output)
    return _Outcome("failed", f"exit {process.returncode}", output)


def _result_text(outcome: _Outcome) -> str:
    """The result line's tail: checked / failed / did not finish / not run."""

    if outcome.decision == "checked":
        return "checked"
    if outcome.decision == "failed":
        return f"failed ({outcome.reason})"
    if outcome.decision == "did-not-finish":
        return f"did not finish ({outcome.reason})"
    return f"not run ({outcome.reason})"


def _run_stages(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        validate_task_id(args.task)
    except JournalRecordError as error:
        print(f"stage run: {error}", file=stderr)
        return 1
    resolved = _resolve(stderr)
    if resolved is None:
        return 1
    placement, state = resolved
    if placement.is_sidecar:
        print(
            "stage run: a sidecar runs no stages — the base its extensions "
            "are taken from is a property of the embedded placement",
            file=stderr,
        )
        return 1
    project_root = placement.project_root
    try:
        resolved_commit = _resolve_commit(project_root, args.commit)
        base_commit = _resolve_commit(project_root, args.base)
        merge_base = _run_git(
            project_root, ["merge-base", base_commit, resolved_commit]
        ).strip()
        manifests = _base_manifests(project_root, merge_base)
    except (GateError, ExtensionManifestError) as error:
        print(f"stage run: {escape_for_display(str(error))}", file=stderr)
        return 1
    modes = _PHASE_MODES[args.phase]
    plan = [
        (name, manifests[name], stage)
        for name in sorted(manifests)
        for stage in manifests[name].stages
        if stage.phase in modes
    ]
    if not plan:
        print(f"stage run: no shared extension declares a {args.phase} stage")
        return 0
    ci = os.environ.get("CI") == "true"
    grants: dict[str, Grant] = {}
    if not ci:
        try:
            grants = _read_grants(state.trust_file)
        except ExtensionTrustError as error:
            print(f"stage run: {escape_for_display(str(error))}", file=stderr)
            return 1
    writer: ProcessLogWriter | None = None
    writer_lost = False

    def record_event(
        name: str, stage: ExtensionStage, outcome: _Outcome, result_text: str
    ) -> None:
        """Append the stage's ``extension-event``; a lost log is a warning.

        The result line and the exit status carry the verdict, so a log
        that cannot be opened or written is named on stderr — never
        silently, and never promoted into a different verdict.
        """

        nonlocal writer, writer_lost
        if writer is None and not writer_lost:
            try:
                writer = open_writer(state)
            except (LocalStateError, ProcessLogError, OSError) as error:
                writer_lost = True
                print(
                    "stage run: cannot open the process log "
                    f"({escape_for_display(str(error))}); results are "
                    "not recorded as events",
                    file=stderr,
                )
        if writer is None:
            return
        # ``result`` rides only on a post-gate event (ADR-0022 section 7's
        # "post-gate results land here carrying a result field"), so the
        # two spellings are passed literally rather than spread. The
        # event's ``reason`` may carry what the result line's own
        # spelling keeps out — the kind of a changed-after-approval
        # difference, for one.
        event_reason = (
            outcome.reason if outcome.event_reason is None else outcome.event_reason
        )
        try:
            if stage.phase == "post-gate":
                write_event(
                    writer,
                    "extension-event",
                    task=args.task,
                    extension=name,
                    scope="shared",
                    phase=stage.phase,
                    decision=outcome.decision,
                    reason=event_reason,
                    commit=resolved_commit,
                    result=result_text,
                )
            else:
                write_event(
                    writer,
                    "extension-event",
                    task=args.task,
                    extension=name,
                    scope="shared",
                    phase=stage.phase,
                    decision=outcome.decision,
                    reason=event_reason,
                    commit=resolved_commit,
                )
        except ProcessLogError as error:
            print(
                f"stage run: the extension-event for "
                f"{escape_for_display(name)} was not recorded: "
                f"{escape_for_display(str(error))}",
                file=stderr,
            )

    paused: list[str] = []
    warnings: list[str] = []
    for index, (name, manifest, stage) in enumerate(plan):
        # Each stage gets its own temporary directory: a stage runs its
        # extension's code with the materialized copy in reach of
        # ``__file__``, so a copy an earlier stage ran against can no
        # longer speak for the base. The directory is materialized
        # afresh and the grant check recomputed on it for every stage,
        # and the copy goes away with the stage's own context.
        with tempfile.TemporaryDirectory(prefix="agentmarshal-stage-") as temporary:
            temp_root = Path(temporary)
            prepared = _prepare_extension(
                project_root, merge_base, name, temp_root, ci, grants
            )
            outcome = _run_stage(
                project_root,
                resolved_commit,
                merge_base,
                args.task,
                args.phase,
                name,
                manifest,
                stage,
                prepared,
                temp_root / f"snapshot-{index}",
            )
        shown = escape_for_display(name)
        text = outcome.output.decode("utf-8", errors="replace")
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        for line in lines:
            print(f"{shown} | {escape_for_display(line)}")
        result_text = _result_text(outcome)
        print(f"{shown}: {result_text}")
        record_event(name, stage, outcome, result_text)
        if stage.phase == "pre-gate-stop" and outcome.decision != "checked":
            paused.append(f"{shown}: {result_text}")
        elif stage.phase == "pre-gate-warn" and outcome.decision != "checked":
            warnings.append(f"{shown}: {result_text}")
    for entry in warnings:
        print(f"stage run: WARNING: extension at pre-gate-warn — {entry}", file=stderr)
    for entry in paused:
        print(
            f"stage run: the process is paused before the gate — {entry}",
            file=stderr,
        )
    return 3 if paused else 0
