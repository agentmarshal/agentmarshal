"""The ``record-check`` command: a pipeline's verdict on a commit.

ADR-0017 decision 1 and ADR-0022 sections 3 and 7: what a pipeline check
found on a commit is evidence — its name, its result, the step that
failed, a short excerpt passed through the leak scan, and a link to the
run — while the full output goes to the process log. ``record-check``
writes one ``check`` record through ``create_check_record``, resolving
``--commit`` to its full 40-hex id in the journal's repository — a
sidecar records against the commits its own repository carries, never
the host's.

``--output-file`` keeps the file's full bytes — unmasked, the masking is
the excerpt's — under the journal repository's local state and announces
them with a ``check-output`` event, the mechanism the review launcher
keeps review prose with. The excerpt is the content's tail: at most the
last 4 KiB, cut on a UTF-8 character boundary with undecodable bytes
replaced — the failing end is the part worth keeping — masked span by
span with ``[masked: <category>]``, escaped for the forgeable-text rule,
and bounded once more to 4 KiB after masking, since a mask can be longer
than what it replaces. A hit is masked, never refused: the check's
result is the fact being recorded, and refusing it over a token printed
in a log would lose the fact with no path to record it.

Every refusal — an unknown task, a commit that does not resolve, a
result outside the vocabulary, a value the record rules refuse, an
unreadable output file — is decided before any write: no record, no
event, no kept file.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.agree import _declared_actor
from agentmarshal.journal.actors import resolve_recorded_by
from agentmarshal.journal.capture import CaptureError, mask_leaks
from agentmarshal.journal.contracts import JournalContractError
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.gate import GateError, markers_from_config
from agentmarshal.journal.placement import (
    Placement,
    PlacementError,
    resolve_placement,
)
from agentmarshal.journal.records import (
    _CHECK_EXCERPT_BYTE_LIMIT,
    _CHECK_RESULTS,
    JournalRecordError,
    _project_root_for,
    create_check_record,
    validate_record_for_write,
    validate_task_id,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from agentmarshal.localstate import LocalStateError, local_state
from agentmarshal.process_log import (
    ProcessLogError,
    open_writer,
    write_event,
    write_payload,
)
from agentmarshal.project import find_project_root

#: The payload prefix the kept output is staged under — a plain file
#: name, so ``write_payload``'s confinement admits it.
_PAYLOAD_PREFIX = "agentmarshal-check-output-"


class RecordCheckError(Exception):
    """Raised when the verdict cannot be recorded, the message naming why."""


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``record-check`` command to *subparsers*."""

    parser = subparsers.add_parser(
        "record-check",
        help="record a pipeline check's verdict on a commit",
    )
    parser.add_argument("--task", required=True, help="task identifier")
    parser.add_argument(
        "--commit",
        required=True,
        help="commit the check ran on — a rev resolved to its full id "
        "in the journal's repository",
    )
    parser.add_argument("--name", required=True, help="name of the check")
    parser.add_argument(
        "--result",
        required=True,
        choices=sorted(_CHECK_RESULTS),
        help="the check's outcome",
    )
    parser.add_argument("--failed-step", help="the pipeline step that failed")
    parser.add_argument("--run-url", help="link to the run at the provider")
    parser.add_argument(
        "--output-file",
        help="the check's full output — kept in local state, its tail "
        "masked into the record's excerpt",
    )


def _placement(stderr: TextIO) -> Placement | None:
    """Resolve the journal placement, or print why it cannot be had."""

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal record-check must be run inside an initialized project",
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


def _resolve_commit(journal_project_root: Path, reference: str) -> str:
    """Resolve *reference* to its full commit id in the journal's repository.

    ``rev-parse --verify <rev>^{commit}`` answers both halves of the rule
    at once: what resolves is the full id, and what does not — a rev the
    repository does not hold, or one naming no commit — fails here rather
    than reaching the record's hex rule with a name it cannot take.
    """

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{reference}^{{commit}}"],
            cwd=journal_project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise RecordCheckError(f"cannot run git: {error}") from error
    resolved = result.stdout.decode("utf-8", errors="replace").strip()
    if result.returncode != 0 or len(resolved) != 40:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        message = (
            f"--commit {escape_for_display(reference)} does not resolve to "
            "a commit in the journal's repository"
        )
        if detail:
            # git's error text is a value the tool did not write — escaped
            # like every displayed string it does not control.
            message += f": {escape_for_display(detail)}"
        raise RecordCheckError(message)
    return resolved


def _bounded_tail(data: bytes) -> str:
    """Decode the last at-most-4-KiB of *data* on a character boundary.

    The byte cut can land inside a multi-byte character; it is moved
    forward past the continuation bytes so no valid character is halved.
    What then fails to decode is replaced — the same ``errors="replace"``
    the diff decoder applies to content that cannot be read.
    """

    tail = data[-_CHECK_EXCERPT_BYTE_LIMIT:]
    start = 0
    while start < len(tail) and tail[start] & 0xC0 == 0x80:
        start += 1
    return tail[start:].decode("utf-8", errors="replace")


def _excerpt(content: bytes, markers: tuple[str, ...]) -> tuple[str, list[str]]:
    """The record's excerpt: the content's masked tail, bounded after masking.

    Masking runs on the text in its true form — a private marker that
    itself carries a newline still matches — and escaping after it
    produces plain ASCII no signature or marker can recompose into. The
    second bound is needed because a ``[masked: …]`` token or an escape
    can be longer than the span it replaces; the excess is dropped from
    the front, so the content's end always survives.
    """

    masked, categories = mask_leaks(_bounded_tail(content), markers)
    escaped = escape_for_display(masked)
    return _bounded_tail(escaped.encode("utf-8")), categories


def _preserve_output(content: bytes) -> Path:
    """Write kept output to a local temporary file — the fallback path.

    Kept output goes under the clone's local state; a temporary file is
    where it lands when the local state cannot be used, exactly as the
    review launcher's kept prose does. The file is deliberately not
    cleaned up; removing it is the caller's decision.
    """

    descriptor, name = tempfile.mkstemp(prefix=_PAYLOAD_PREFIX, suffix=".txt")
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)
    return Path(name)


def _keep_output(
    placement: Placement,
    task_id: str,
    name: str,
    commit: str,
    content: bytes,
) -> tuple[Path | None, str]:
    """Keep the output under the journal repository's local state.

    The file lands in ``log/files/`` — the process-log area — and a
    ``check-output`` event names the task, the check, the resolved
    commit, the file and its sha256: the mechanism the review launcher
    keeps prose with (ADR-0014 decision 5, ADR-0022 section 7). Returns
    ``(kept path, note for stderr)``; when the local state cannot be
    used the output falls back to a temporary file and the note says
    why — a check's result is never discarded because preservation
    failed.
    """

    try:
        state = local_state(placement)
        kept = write_payload(state, _PAYLOAD_PREFIX, content)
        write_event(
            open_writer(state),
            "check-output",
            task=task_id,
            name=name,
            commit=commit,
            path=str(kept),
            sha256=hashlib.sha256(content).hexdigest(),
        )
    except (LocalStateError, ProcessLogError, OSError) as error:
        reason = (
            error.strerror or str(error) if isinstance(error, OSError) else str(error)
        )
        try:
            kept = _preserve_output(content)
        except OSError as inner:
            return None, (
                f"check output could not be kept locally ({inner}); the "
                "clone's local state could not be used either "
                f"({escape_for_display(reason)})"
            )
        return kept, (
            f"check output kept at {escape_for_display(str(kept))}; the "
            "clone's local state could not be used "
            f"({escape_for_display(reason)})"
        )
    return kept, f"check output kept at {escape_for_display(str(kept))}"


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Record one pipeline check's verdict on a commit."""

    try:
        validate_task_id(args.task)
    except JournalRecordError as error:
        print(f"record-check: {error}", file=stderr)
        return 1
    placement = _placement(stderr)
    if placement is None:
        return 1
    journal_root = placement.journal_root
    try:
        load_task_for_record(journal_root, args.task, "check")
        resolved = _resolve_commit(placement.project_root, args.commit)
        content: bytes | None = None
        if args.output_file is not None:
            try:
                content = Path(args.output_file).read_bytes()
            except OSError as error:
                raise RecordCheckError(
                    f"cannot read --output-file "
                    f"{escape_for_display(args.output_file)}: "
                    f"{escape_for_display(error.strerror or str(error))}"
                ) from error
            try:
                markers = markers_from_config(placement.project_root)
            except (GateError, CaptureError, ValueError) as error:
                raise RecordCheckError(
                    f"cannot read project configuration: {error}"
                ) from error
        else:
            markers = ()
        # The record requires its recorder, so the resolution the record
        # rules would refuse on is decided here, before anything is
        # written — on the same root `write_record` resolves it from.
        recorder_root = _project_root_for(journal_root)
        actor = resolve_recorded_by(recorder_root)
        if actor is None:
            raise RecordCheckError(
                "no recorder identity could be resolved; set "
                "AGENTMARSHAL_ACTOR or configure git user.email"
            )
        recorder, source = actor
        excerpt: str | None = None
        categories: list[str] = []
        if content is not None:
            candidate, categories = _excerpt(content, markers)
            # The record admits `excerpt` only as a non-empty string, so
            # an output whose tail holds nothing worth keeping — an
            # empty file, whitespace — carries none.
            if candidate.strip():
                excerpt = candidate
        record = create_check_record(
            args.task,
            __version__,
            resolved,
            args.name,
            args.result,
            failed_step=args.failed_step,
            excerpt=excerpt,
            run_url=args.run_url,
        )
        # Every refusal knowable before an exclusive write — the record's
        # shape, the forgeable-text rule, the schema — lands here, before
        # the payload, the event and the record itself, so a refused run
        # leaves the journal, the log and the files area untouched.
        validate_record_for_write(journal_root, args.task, record)
        kept: Path | None = None
        note: str | None = None
        if content is not None:
            kept, note = _keep_output(
                placement, args.task, args.name, resolved, content
            )
        try:
            record_path = write_record(journal_root, args.task, record)
        except (JournalRecordError, OSError, ValueError) as error:
            detail = str(error)
            if kept is not None:
                detail += f"; check output left at {escape_for_display(str(kept))}"
            raise RecordCheckError(detail) from error
    except (RecordCheckError, JournalContractError) as error:
        print(f"record-check: {error}", file=stderr)
        return 1
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print(f"commit {resolved}")
    print(f"check {args.name}")
    print(f"result {args.result}")
    print(f"recorded by {escape_for_display(recorder)}")
    if categories:
        print(
            f"record-check: excerpt masked: {', '.join(categories)}",
            file=stderr,
        )
    if note is not None:
        print(note, file=stderr)
    if not _declared_actor(recorder_root, recorder, source):
        print(
            f"note: {escape_for_display(recorder)} is not a declared actor",
            file=stderr,
        )
    return 0
