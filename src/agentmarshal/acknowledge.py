"""The ``acknowledge`` command: a reviewed leak-scan hit, on the record.

ADR-0021 and ADR-0022 section 3: an operator who has verified a hit the
added-content scan reported records an ``acknowledgement`` bound to the
candidate's commit, the file and the hit's identification exactly as the
scan prints it — a signature id or ``private-marker #N``, never the
matched text — with a reason. ``acknowledge`` writes one
``acknowledgement`` record through ``create_acknowledgement_record``,
``--commit`` resolved to its full 40-hex id in the scanned repository —
the host's under a sidecar, where the candidate's commits live.

A record naming a hit the scan never reported would match nothing and
say something false, so before writing the command runs the same
added-content scan ``agentmarshal leak-scan --base --commit`` runs:
the same merge base in the scanned repository, the project's private
markers read from the same trusted side, the same per-file-decoded diff
through ``leak_scan_diff``, and the hits through ``scan_diff_for_leaks``
— the same functions over the same inputs, never a second scan. It
writes only when a hit's file equals ``--file`` exactly — as the scan
prints it, masking included — and its identification equals
``--signature``, or ``private-marker #<n>`` for ``--marker <n>``; a
mismatch is a refusal naming the file and the identification given and
how many hits the scan did report, never the matched text.

Every refusal — an unknown or terminal task, a commit or base that does
not resolve, both or neither of ``--signature`` and ``--marker``, a
value the record rules refuse, a ``--reason`` that trips the scan, a
hit the scan does not report — is decided before any write: no record.
A written record is honoured on the hit's surfaces (ADR-0021 decision
3): ``leak-scan`` prints the hit marked and no longer fails on its
account, and the gate's advisory line carries the same mark.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.agree import _declared_actor
from agentmarshal.commits import CommitResolutionError, resolve_commit
from agentmarshal.journal.actors import resolve_recorded_by
from agentmarshal.journal.capture import (
    CaptureError,
    render_undecodable_files,
    safe_path,
    scan_diff_for_leaks,
    scan_for_leaks,
)
from agentmarshal.journal.contracts import JournalContractError
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.gate import (
    GateError,
    leak_scan_diff,
    markers_from_config,
    markers_from_tree,
)
from agentmarshal.journal.placement import (
    Placement,
    PlacementError,
    resolve_placement,
)
from agentmarshal.journal.records import (
    JournalRecordError,
    _project_root_for,
    create_acknowledgement_record,
    validate_record_for_write,
    validate_task_id,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from agentmarshal.project import PROJECT_CONFIG_RELPATH, find_project_root


class AcknowledgeError(Exception):
    """Raised when the hit cannot be acknowledged, the message naming why."""


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``acknowledge`` command to *subparsers*."""

    parser = subparsers.add_parser(
        "acknowledge",
        help="record that a reported leak-scan hit was reviewed",
    )
    parser.add_argument("--task", required=True, help="task identifier")
    parser.add_argument(
        "--base", required=True, help="merge target ref (the comparison base)"
    )
    parser.add_argument(
        "--commit", required=True, help="candidate head ref the hit was found in"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="the file exactly as the scan's hit prints it — a path "
        "carrying a marker is named in its masked form",
    )
    identification = parser.add_mutually_exclusive_group(required=True)
    identification.add_argument(
        "--signature", help="the built-in signature's identifier"
    )
    identification.add_argument(
        "--marker",
        type=int,
        help="the private marker's one-based position in the configured list",
    )
    parser.add_argument(
        "--reason", required=True, help="why the reported hit is not a leak"
    )


def _placement(stderr: TextIO) -> Placement | None:
    """Resolve the journal placement, or print why it cannot be had."""

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal acknowledge must be run inside an initialized project",
            file=stderr,
        )
        return None
    try:
        # The host is required: it is the repository whose diff the scan
        # reads, which is the project's own root in the embedded placement
        # and the sidecar's host otherwise.
        return resolve_placement(project_root, require_host=True)
    except PlacementError as error:
        # The message can carry a value the tool did not write — a host
        # path from project.json, git's own error text — so it is escaped
        # the way a transcript line is, as cli.py's placement does.
        print(escape_for_display(str(error)), file=stderr)
        return None


def _merge_base(scan_root: Path, base: str, commit: str) -> str:
    """The merge base of *base* and *commit* in the scanned repository.

    The same invocation ``leak-scan`` makes for the same refs, so the
    range scanned here is the range it reports — a ref that does not
    resolve, or no common ancestor, is refused naming both references.
    """

    try:
        result = subprocess.run(
            ["git", "merge-base", base, commit],
            cwd=scan_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise AcknowledgeError(f"cannot run git: {error}") from error
    merge_base = result.stdout.decode("utf-8", errors="replace").strip()
    if result.returncode != 0 or not merge_base:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        message = (
            f"cannot find the merge base of {escape_for_display(base)} and "
            f"{escape_for_display(commit)}"
        )
        if detail:
            message += f": {escape_for_display(detail)}"
        raise AcknowledgeError(message)
    return merge_base


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Record that a reported leak-scan hit was reviewed."""

    try:
        validate_task_id(args.task)
    except JournalRecordError as error:
        print(f"acknowledge: {error}", file=stderr)
        return 1
    placement = _placement(stderr)
    if placement is None:
        return 1
    journal_root = placement.journal_root
    # The scan reads the repository the candidate's commits live in — the
    # host under a sidecar — and the configured markers come from the
    # trusted side exactly as `leak-scan` reads them: the sidecar's own
    # configuration there, the merge-base tree in the embedded placement.
    scan_root = placement.host_root
    sidecar_config = placement.project_root if placement.is_sidecar else None
    try:
        load_task_for_record(journal_root, args.task, "acknowledgement")
        try:
            resolved = resolve_commit(
                scan_root, args.commit, repository="the scanned repository"
            )
        except CommitResolutionError as error:
            raise AcknowledgeError(str(error)) from error
        merge_base = _merge_base(scan_root, args.base, args.commit)
        # The record requires its recorder, so the resolution the record
        # rules would refuse on is decided here, before anything is
        # written — on the same root `write_record` resolves it from.
        recorder_root = _project_root_for(journal_root)
        actor = resolve_recorded_by(recorder_root)
        if actor is None:
            raise AcknowledgeError(
                "no recorder identity could be resolved; set "
                "AGENTMARSHAL_ACTOR or configure git user.email"
            )
        recorder, source = actor
        record = create_acknowledgement_record(
            args.task,
            __version__,
            resolved,
            args.file,
            args.reason,
            signature=args.signature,
            marker=args.marker,
        )
        # Every record refusal knowable before a write — the signature
        # vocabulary, `marker` at least 1, the reason's bound, the
        # forgeable-text rule — lands here, before the hit is matched, so
        # a value the record rules refuse is refused on the rule rather
        # than reported as a hit the scan does not report.
        validate_record_for_write(journal_root, args.task, record)
        try:
            markers = (
                markers_from_config(sidecar_config)
                if sidecar_config is not None
                else markers_from_tree(scan_root, merge_base)
            )
        except (GateError, CaptureError, ValueError) as error:
            raise AcknowledgeError(f"cannot read project config: {error}") from error
        # The reason lands in the record, so it passes the same text
        # scan any kept text passes, with the same markers: a hit is a
        # refusal naming the categories — never the matched text — and
        # the operator re-words the reason rather than masking it.
        reason_categories = scan_for_leaks(args.reason, markers)
        if reason_categories:
            raise AcknowledgeError(
                f"--reason refused: possible secrets detected "
                f"({', '.join(reason_categories)}); re-word the reason"
            )
        try:
            diff_text, undecodable = leak_scan_diff(scan_root, merge_base, args.commit)
        except GateError as error:
            raise AcknowledgeError(f"git diff failed: {error}") from error
        hits = scan_diff_for_leaks(
            diff_text,
            markers,
            config_path="" if sidecar_config is not None else PROJECT_CONFIG_RELPATH,
        )
        # Files that did not decode are a caveat about the scan, reported
        # the way the standalone command reports them: their bytes were
        # still searched, and a partial read is no hit and fails nothing.
        if undecodable:
            print(
                "acknowledge: could not decode as UTF-8 "
                "(added bytes still searched): "
                + render_undecodable_files(undecodable, markers, limit=None),
                file=stderr,
            )
        # The match is the hit exactly as the scan prints it: `hit.path`
        # is already masked, so a file carrying a marker is named by its
        # printed masked form; the identification is the signature id or
        # `private-marker #N`. No normalisation, no globbing — a spelling
        # the scan never printed matches nothing.
        identification = (
            args.signature
            if args.signature is not None
            else f"private-marker #{args.marker}"
        )
        if not any(
            hit.path == args.file and hit.identification == identification
            for hit in hits
        ):
            # The refusal names the file as given — masked the way every
            # path the tool prints is masked, since a misspelt masked
            # form could itself carry the marker's value — and the
            # identification, plus the count of hits the scan reported.
            raise AcknowledgeError(
                f"no reported hit names --file "
                f"{escape_for_display(safe_path(args.file, markers))} "
                f"with {'--signature' if args.signature is not None else '--marker'} "
                f"{escape_for_display(identification)}: the scan reported "
                f"{len(hits)} {'hit' if len(hits) == 1 else 'hits'}"
            )
        record_path = write_record(journal_root, args.task, record)
    except (AcknowledgeError, JournalContractError) as error:
        print(f"acknowledge: {error}", file=stderr)
        return 1
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print(f"commit {resolved}")
    print(f"file {args.file}")
    if args.signature is not None:
        print(f"signature {args.signature}")
    else:
        print(f"marker {args.marker}")
    print(f"recorded by {escape_for_display(recorder)}")
    if not _declared_actor(recorder_root, recorder, source):
        print(
            f"note: {escape_for_display(recorder)} is not a declared actor",
            file=stderr,
        )
    return 0
