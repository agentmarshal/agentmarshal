"""The ``record-ext`` command: a shared extension's result, on the record.

ADR-0013 decision 18 and ADR-0022 sections 3 and 8: extension records are
a shared ``ext`` type — the core knows the envelope, the kind carries a
namespace and a version, the body is opaque to the core, hash-pinned and
size-limited — and only a shared extension writes ``ext``, never to the
journal directly: the record goes through the core's command, which
writes the envelope. ``record-ext`` writes one ``ext`` record through
``create_ext_record``, resolving ``--commit`` to its full 40-hex id in
the journal's repository — a sidecar records against the commits its own
repository carries, never the host's.

The kind lands only when the shared extension ``<name>``'s manifest in
the journal repository's working tree declares it in ``[records].kinds``
— the file form or the directory form, read through
``read_extension_manifest`` with its symlink rules. A kind not of the
``<name>/<kind>@<version>`` form, a kind no manifest declares and a
manifest that cannot be read each refuse the write naming the kind.

The payload is read as JSON from ``--payload-file`` and leak-scanned at
write with the project's configured private markers — the same
``markers_from_config`` read ``record-check`` makes. Every string in it —
every string value and every object key, at any depth — is masked through
``mask_leaks``: each matched span becomes ``[masked: <category>]`` and
the command names the categories, never the matched text. The hash is
computed after masking — ``payload_sha256`` pins what the record
carries — and a masked canonical form that still trips the scan, or
exceeds 64 KiB, is refused: there is no excerpt to withhold the way
``record-check`` withholds one, the payload is the record.

Every refusal — an unknown or terminal task, a commit that does not
resolve, a kind no shared extension declares, a manifest that cannot be
read, an unreadable or non-JSON payload file, a payload that stays
unclean or too large after masking, no resolvable recorder — is decided
before any write: no record.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.agree import _declared_actor
from agentmarshal.journal.actors import resolve_recorded_by
from agentmarshal.journal.capture import CaptureError, mask_leaks, scan_for_leaks
from agentmarshal.journal.contracts import JournalContractError
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    _RECORD_KIND,
    ExtensionManifestError,
    read_extension_manifest,
)
from agentmarshal.journal.gate import GateError, markers_from_config
from agentmarshal.journal.placement import (
    Placement,
    PlacementError,
    resolve_placement,
)
from agentmarshal.journal.records import (
    _EXT_PAYLOAD_BYTE_LIMIT,
    JournalRecordError,
    _canonical_json,
    _project_root_for,
    create_ext_record,
    validate_record_for_write,
    validate_task_id,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from agentmarshal.project import find_project_root


class RecordExtError(Exception):
    """Raised when the extension's result cannot be recorded, naming why."""


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``record-ext`` command to *subparsers*."""

    parser = subparsers.add_parser(
        "record-ext",
        help="record a shared extension's result on a task",
    )
    parser.add_argument("--task", required=True, help="task identifier")
    parser.add_argument(
        "--commit",
        required=True,
        help="commit the result binds — a rev resolved to its full id "
        "in the journal's repository",
    )
    parser.add_argument(
        "--kind",
        required=True,
        help="the record kind — '<name>/<kind>@<version>', declared in "
        "the shared extension <name>'s manifest",
    )
    parser.add_argument(
        "--payload-file",
        required=True,
        help="the extension's result as JSON — leak-scanned at write",
    )


def _placement(stderr: TextIO) -> Placement | None:
    """Resolve the journal placement, or print why it cannot be had."""

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal record-ext must be run inside an initialized project",
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
        raise RecordExtError(f"cannot run git: {error}") from error
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
        raise RecordExtError(message)
    return resolved


def _declared_kind(project_root: Path, kind: str) -> None:
    """Require *kind* to be one `<name>`'s manifest declares.

    `<name>` is the kind's first segment; its manifest — either form —
    is the shared scope's declaration of the kinds the extension writes
    (ADR-0013 decision 18). The form rule is the manifest's own, imported
    rather than copied, so a value no manifest could declare is refused
    before a manifest is looked for.
    """

    if _RECORD_KIND.fullmatch(kind) is None:
        raise RecordExtError(
            f"--kind {escape_for_display(kind)} must be of the form "
            "'<name>/<kind>@<version>'"
        )
    name = kind.split("/", 1)[0]
    try:
        manifest = read_extension_manifest(project_root, name)
    except ExtensionManifestError as error:
        # A missing manifest and an unreadable one land the same refusal
        # — the kind is declared by no shared extension the command can
        # read — the manifest's own message saying which.
        raise RecordExtError(
            f"--kind {escape_for_display(kind)}: {escape_for_display(str(error))}"
        ) from error
    if kind not in manifest.record_kinds:
        raise RecordExtError(
            f"--kind {escape_for_display(kind)} is not declared in "
            f"[records].kinds of extension {escape_for_display(name)!r}'s "
            "manifest"
        )


def _read_payload(path: str) -> object:
    """Read and parse the payload file as JSON, refusing what neither does."""

    try:
        content = Path(path).read_bytes()
    except OSError as error:
        raise RecordExtError(
            f"cannot read --payload-file {escape_for_display(path)}: "
            f"{escape_for_display(error.strerror or str(error))}"
        ) from error
    try:
        return json.loads(content)
    except ValueError as error:
        raise RecordExtError(
            f"--payload-file {escape_for_display(path)} is not JSON: "
            f"{escape_for_display(str(error))}"
        ) from error


def _mask_payload(
    payload: object, markers: tuple[str, ...]
) -> tuple[object, list[str]]:
    """Every string in *payload* masked, object keys included.

    A secret can hide anywhere in the body — a member's name is a string
    like any other — so masking runs over keys with the values, at any
    depth. Two keys that mask to one are refused: the collapse would
    silently drop a member, and the masked key is never echoed — it can
    still carry a marker's value in its label.
    """

    categories: set[str] = set()
    masked = _mask_value(payload, markers, categories)
    return masked, sorted(categories)


def _mask_value(
    value: object, markers: tuple[str, ...], categories: set[str]
) -> object:
    if isinstance(value, str):
        masked, found = mask_leaks(value, markers)
        categories.update(found)
        return masked
    if isinstance(value, list):
        return [_mask_value(item, markers, categories) for item in value]
    if isinstance(value, dict):
        masked_object: dict[str, object] = {}
        for key, item in value.items():
            masked_key, found = mask_leaks(key, markers)
            categories.update(found)
            if masked_key in masked_object:
                raise RecordExtError(
                    "payload refused: masking merges two object keys; "
                    "rename them so each stays distinct"
                )
            masked_object[masked_key] = _mask_value(item, markers, categories)
        return masked_object
    return value


def _clean_canonical(
    masked: object, markers: tuple[str, ...], categories: list[str]
) -> None:
    """The masked payload's canonical form: bounded, and clean under the scan.

    The canonical form is the one byte sequence the 64 KiB bound and the
    hash measure, so both checks run on it — never on the file as given.
    The rescan is the masking function's own caveat made a rule: a marker
    occurring in the mask label itself, or spanning a boundary no single
    string holds, still trips the scan, and then there is no excerpt to
    withhold — the payload is the record, so the write is refused naming
    the categories either scan found.
    """

    try:
        canonical = _canonical_json(masked)
    except (TypeError, ValueError) as error:
        raise RecordExtError(
            "ext record field 'payload' must be a JSON value"
        ) from error
    if len(canonical) > _EXT_PAYLOAD_BYTE_LIMIT:
        raise RecordExtError(
            f"payload refused: the canonical form is {len(canonical)} bytes; "
            f"the bound is {_EXT_PAYLOAD_BYTE_LIMIT}"
        )
    remaining = scan_for_leaks(canonical.decode("utf-8"), markers)
    if remaining:
        named = sorted(set(categories) | set(remaining))
        raise RecordExtError(
            f"payload refused: masking could not make it clean ({', '.join(named)})"
        )


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Record one shared extension's result on a task."""

    try:
        validate_task_id(args.task)
    except JournalRecordError as error:
        print(f"record-ext: {error}", file=stderr)
        return 1
    placement = _placement(stderr)
    if placement is None:
        return 1
    journal_root = placement.journal_root
    try:
        load_task_for_record(journal_root, args.task, "ext")
        resolved = _resolve_commit(placement.project_root, args.commit)
        _declared_kind(placement.project_root, args.kind)
        payload = _read_payload(args.payload_file)
        try:
            markers = markers_from_config(placement.project_root)
        except (GateError, CaptureError, ValueError) as error:
            raise RecordExtError(
                f"cannot read project configuration: {error}"
            ) from error
        masked, categories = _mask_payload(payload, markers)
        _clean_canonical(masked, markers, categories)
        # The record requires its recorder, so the resolution the record
        # rules would refuse on is decided here, before anything is
        # written — on the same root `write_record` resolves it from.
        recorder_root = _project_root_for(journal_root)
        actor = resolve_recorded_by(recorder_root)
        if actor is None:
            raise RecordExtError(
                "no recorder identity could be resolved; set "
                "AGENTMARSHAL_ACTOR or configure git user.email"
            )
        recorder, source = actor
        record = create_ext_record(args.task, __version__, args.kind, resolved, masked)
        # Every refusal knowable before an exclusive write — the record's
        # shape, the kind's forgeable-text rule, the schema — lands here,
        # so a refused run leaves the journal untouched.
        validate_record_for_write(journal_root, args.task, record)
        record_path = write_record(journal_root, args.task, record)
    except (RecordExtError, JournalContractError) as error:
        print(f"record-ext: {error}", file=stderr)
        return 1
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        print(error, file=stderr)
        return 1
    print(record_path)
    print(f"commit {resolved}")
    print(f"kind {args.kind}")
    print(f"payload sha256 {record['payload_sha256']}")
    print(f"recorded by {escape_for_display(recorder)}")
    if categories:
        print(
            f"record-ext: payload masked: {', '.join(categories)}",
            file=stderr,
        )
    if not _declared_actor(recorder_root, recorder, source):
        print(
            f"note: {escape_for_display(recorder)} is not a declared actor",
            file=stderr,
        )
    return 0
