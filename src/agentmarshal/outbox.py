"""The ``outbox`` command group: finding drafts for upstream.

ADR-0020 decisions 1-5: one command group named ``outbox`` covers the life
of a finding for upstream; ``finding`` stays the journal command of
ADR-0009. ``outbox new`` scaffolds a draft carrying the five fields of
CONTRIBUTING's finding form, Version and Environment filled from the
machine. ``outbox check`` names, per draft, the file and each missing or
still-unfilled field, runs the merge boundary's leak scan over what would
be sent, and refuses by exit status so a batch wrapper can refuse to send.
``outbox send`` runs that check, stages only the outbox, verifies the
staged blobs are what the check vetted and makes one batch commit —
delivery stays with the operator. ``outbox status`` hashes
the outbox files and compares them with the ``Source:`` lines of an index
file the operator passes. ``check`` and ``send`` use the same matching —
plus the outbox's own sent manifest, ``SENT``, which ``send`` updates in
the batch commit — to treat a file already sent as no draft; and when no
draft is new, ``send`` still commits a rename or a move of a file
already sent — the manifest following the new name — and refuses any
other change it finds with no draft as no drafts. The group opens no
network.

The outbox is ``project_root/.agentmarshal/upstream`` — the directory
``init`` scaffolds beside ``project.json`` — which is the same expression
in both placements: in an embedded project it is the host repository's
``.agentmarshal``, in a sidecar the journal repository's, so a batch
commit lands in the journal repository and never touches the host. Every
subcommand refuses a symbolic link at ``.agentmarshal`` or ``upstream``
before creating or writing anything — a linked outbox would write
wherever the link points — and the check ``send`` runs first refuses a
file git's attributes would transform on staging, so only the bytes the
check vetted are ever committed.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import NamedTuple, TextIO

from agentmarshal import __version__
from agentmarshal.journal.capture import (
    CaptureError,
    LeakHit,
    render_leak_hits,
    safe_path,
    scan_for_leaks,
)
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.gate import GateError, markers_from_config
from agentmarshal.journal.records import forges_rendered_text
from agentmarshal.project import PROJECT_DIR_NAME, find_project_root

_UPSTREAM_DIR = "upstream"
_README = "README.md"
# The sent manifest: a file in the outbox, one `<sha256>  <name>` line
# per file sent — the sha256sum output form, so an adopter's own record
# of a batch can become it by hand. The name cannot be mistaken for a
# draft: no `.md` suffix, no `NNNN-` number, uppercase like the README.
_SENT = "SENT"
# The manifest is parsed strictly: 64 lowercase hex digits, exactly two
# spaces, then the name — which must be free of the characters that could
# forge a line, so one line is one entry and a name can never inject a
# second one. A line in any other shape — or a line that is not UTF-8 at
# all — does not parse and refuses the command.
_SENT_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")
# The outbox as a repository-relative path and as the prefix staged paths
# carry: `.agentmarshal/upstream` — the README's exclude pathspec applied
# the other way.
_OUTBOX_DIR_SPEC = f"{PROJECT_DIR_NAME}/{_UPSTREAM_DIR}"
_OUTBOX_PREFIX = f"{_OUTBOX_DIR_SPEC}/"

# The five fields of CONTRIBUTING's "Reporting a finding", in its order,
# with the hint each carries there. The hint is also the scaffold's
# placeholder: a section left as written is unfilled.
_FIELDS = ("Symptom", "Measurements", "Version", "Environment", "Expected")
_FIELD_HINTS = {
    "Symptom": "what you observed, with the exact command and its output",
    "Measurements": 'counts, timings, how often it happens (e.g. "3 of 7 runs")',
    "Version": "output of `agentmarshal --version`",
    "Environment": "OS, Python version, git provider (GitHub / GitFlic / self-hosted)",
    "Expected": "what you expected instead, and why",
}

# A name counts toward the next number in the exact shape `new` writes:
# `NNNN` as `:04d` emits it — zero-padded to four digits below 1000,
# unpadded at and above it — then `-` and a slug. Whatever digit groups
# the slug opens with, the name still counts: `new` itself emits `-NN-NN-`
# after the number (the gist "12 34 widget" slugs to `12-34-widget`), so a
# digit-led slug must not hide a draft. The one exception is the date a
# hand writes: an unpadded four-digit number followed by a valid `-MM-DD-`
# reads as a date prefix, so `2026-10-03-note.md` is not number 2026 —
# while `new`'s zero padding keeps `0001-10-03-note.md` a number, since no
# hand-written date opens `0NNN`.
_DRAFT_NAME = re.compile(r"^(0\d{3}|[1-9]\d{3,})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_DATE_NAME = re.compile(
    r"^[1-9]\d{3}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])(?:-|\.md$)"
)
_HEADING = re.compile(r"^## (.+?)\s*$")
_SLUG_RUN = re.compile(r"[^a-z0-9]+")
_SLUG_MAX = 60


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``outbox`` group and its subcommands to *subparsers*."""

    outbox_parser = subparsers.add_parser(
        "outbox", help="scaffold, check, send and report finding drafts"
    )
    outbox_commands = outbox_parser.add_subparsers(dest="outbox_command", required=True)
    new_parser = outbox_commands.add_parser(
        "new", help="scaffold a finding draft in the outbox"
    )
    new_parser.add_argument("gist", help="one-line gist naming the finding")
    check_parser = outbox_commands.add_parser(
        "check", help="name what the drafts lack and what the leak scan finds"
    )
    check_parser.add_argument(
        "--index",
        type=Path,
        help="file whose Source: lines name digests already sent",
    )
    send_parser = outbox_commands.add_parser(
        "send", help="check, then commit the outbox as one batch"
    )
    send_parser.add_argument(
        "--index",
        type=Path,
        help="file whose Source: lines name digests already sent",
    )
    status_parser = outbox_commands.add_parser(
        "status", help="report which outbox files an index file claims"
    )
    status_parser.add_argument(
        "--index",
        required=True,
        type=Path,
        help="file whose Source: lines name published digests",
    )


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Dispatch the parsed ``outbox`` subcommand."""

    if args.outbox_command == "new":
        return _run_new(args.gist, stderr)
    if args.outbox_command == "check":
        return _run_check(args.index, stderr)
    if args.outbox_command == "send":
        return _run_send(args.index, stderr)
    if args.outbox_command == "status":
        return _run_status(args.index, stderr)
    print(f"outbox: unknown command {args.outbox_command}", file=stderr)
    return 1


def _locate(command: str, stderr: TextIO) -> tuple[Path, Path] | None:
    """Return the project root and outbox, or print why there is none."""

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            f"agentmarshal outbox {command} must be run inside an initialized project",
            file=stderr,
        )
        return None
    outbox = project_root / PROJECT_DIR_NAME / _UPSTREAM_DIR
    # Every component below the resolved project root is judged with
    # lstat before anything is created, written or staged: a linked
    # `.agentmarshal` or `upstream` would land the outbox's files
    # wherever the link points — in a sidecar the host — which the
    # threat model forbids. The same refusal `extension_trust` applies
    # to the managed extensions directory.
    for component in (outbox.parent, outbox):
        if component.is_symlink():
            # The line is masked like every path this group prints — a
            # directory on the outbox's path can itself carry a marker —
            # so the markers must load first; when they cannot, the
            # refusal `_markers` already printed stands in for this one.
            markers = _markers(command, project_root, stderr)
            if markers is None:
                return None
            print(
                f"outbox {command}: refusing a symbolic link: "
                f"{_printable(component, markers)}",
                file=stderr,
            )
            return None
    if not outbox.is_dir():
        print(
            f"outbox {command}: no outbox — init scaffolds "
            f"{PROJECT_DIR_NAME}/{_UPSTREAM_DIR}/ under the project root",
            file=stderr,
        )
        return None
    return project_root, outbox


def _os_error_text(error: OSError) -> str:
    """A fixed description of an OS error — never ``str(error)``.

    ``str(OSError)`` carries the path it failed on; ``strerror`` is the
    system's text for the errno and names nothing.
    """

    if error.strerror:
        return error.strerror
    if error.errno is not None:
        return errno.errorcode.get(error.errno, type(error).__name__)
    return type(error).__name__


def _config_error_text(error: GateError) -> str:
    """Describe a failed config read without quoting the GateError's text.

    ``markers_from_config`` wraps the real error in a message carrying the
    path it failed on; the cause is described by errno text or by name —
    ``read_project_file``'s own ``ValueError`` embeds the path too, so no
    exception's text is ever quoted.
    """

    cause = error.__cause__
    if isinstance(cause, OSError):
        return _os_error_text(cause)
    if cause is not None:
        return type(cause).__name__
    return "unreadable"


def _shown_name(name: str | bytes | os.PathLike[str]) -> str:
    """The printable form of a file name or path.

    ``os.fsencode`` reverses the surrogateescape decode the filesystem
    layer applied — and passes bytes through — so a ``backslashreplace``
    decode writes one ``\\xNN`` escape per undecodable byte: the escaped
    printable form the leak scan uses for undecodable diff header lines.
    The surrogate-carrying ``str`` a non-UTF-8 name arrives as could not
    be printed at all; this form can, and is also what the name scan and
    the marker masking see.
    """

    return os.fsencode(name).decode("utf-8", errors="backslashreplace")


def _printable(name: str | bytes | os.PathLike[str], markers: tuple[str, ...]) -> str:
    """The name as a command line prints it: masked first, then escaped.

    The masking must see the raw shown name — escaping first inserts
    word characters (``\\t`` for a tab, ``\\uXXXX`` for the rest) that
    defeat the signatures' ``\\b`` and ``\\s`` anchors, so a secret
    beside a control character would print unmasked. The masked, escaped
    form is what prints: no marker's value, no matched text, and no
    character that could add a line. ``escape_for_display`` renders a
    newline as ``\\n``, every other refused character as ``\\uXXXX``, and
    leaves every other character — including the ``\\xNN`` escapes a
    non-UTF-8 name already carries — as it is.
    """

    return escape_for_display(safe_path(_shown_name(name), markers))


def _markers(
    command: str, project_root: Path, stderr: TextIO
) -> tuple[str, ...] | None:
    """The configured private markers, or a printed refusal.

    A malformed ``leak_scan`` section is a fixed diagnosis: the
    ``CaptureError``'s text echoes the unknown configured keys, so no part
    of the exception's text is printed; a failed read is described without
    the ``GateError``'s path-carrying text, like every error in this
    group.
    """

    try:
        return markers_from_config(project_root)
    except CaptureError:
        # A malformed leak_scan section is a fixed diagnosis: the
        # CaptureError's text echoes the unknown configured keys, so no
        # part of the exception's text is printed.
        print(
            f"outbox {command}: the leak-scan configuration in project.json "
            "is malformed; run `agentmarshal doctor`",
            file=stderr,
        )
    except GateError as error:
        print(
            f"outbox {command}: cannot read project config: "
            f"{_config_error_text(error)}",
            file=stderr,
        )
    return None


# --- `outbox new` ---------------------------------------------------------


def _slug(gist: str) -> str:
    """A filename-safe slug of the gist; ``draft`` when nothing survives.

    Reports may arrive in any language, and a non-Latin alphabet slugs to
    empty — that is a gist the fallback names, not an error.
    """

    slug = _SLUG_RUN.sub("-", gist.lower()).strip("-")
    slug = slug[:_SLUG_MAX].rstrip("-")
    return slug or "draft"


def _placeholder(field: str) -> str:
    """The scaffold's per-field placeholder: the CONTRIBUTING hint as a comment."""

    return f"<!-- {_FIELD_HINTS[field]} -->"


def _field_value(field: str) -> str:
    if field == "Version":
        return __version__
    if field == "Environment":
        return f"{platform.platform()}, Python {platform.python_version()}"
    return _placeholder(field)


def _render_draft(gist: str) -> str:
    parts = [f"# {gist.strip().splitlines()[0]}", ""]
    for field in _FIELDS:
        parts += [f"## {field}", "", _field_value(field), ""]
    return "\n".join(parts)


def _write_draft(outbox: Path, slug: str, text: str) -> Path:
    """Write *text* as the next free ``NNNN-<slug>.md``, never overwriting.

    The number is one more than the largest already used — monotonic, so a
    gap a removed draft left is never refilled and name order stays
    creation order. Creation is exclusive; a collision — a race, or a file
    placed by hand — advances the number rather than truncating what is
    there.
    """

    used = [
        int(match.group(1))
        for entry in outbox.iterdir()
        if (match := _DRAFT_NAME.match(entry.name)) and not _DATE_NAME.match(entry.name)
    ]
    number = max(used, default=0)
    while True:
        number += 1
        draft = outbox / f"{number:04d}-{slug}.md"
        try:
            with draft.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        except FileExistsError:
            continue
        return draft


def _run_new(gist: str, stderr: TextIO) -> int:
    if not gist.strip():
        print("outbox new: the gist must not be empty", file=stderr)
        return 1
    located = _locate("new", stderr)
    if located is None:
        return 1
    _, outbox = located
    try:
        draft = _write_draft(outbox, _slug(gist), _render_draft(gist))
    except OSError as error:
        print(
            f"outbox new: cannot write the draft: {_os_error_text(error)}",
            file=stderr,
        )
        return 1
    print(draft)
    return 0


# --- `outbox check` --------------------------------------------------------


def _field_bodies(text: str) -> dict[str, list[str]]:
    """Map each level-2 heading to its stripped bodies, in order.

    Split on ``"\\n"`` only: it is the one line separator in a text file,
    and ``str.splitlines`` would also break a draft at control characters
    and miscount a body around them.
    """

    bodies: dict[str, list[list[str]]] = {}
    current: list[str] | None = None
    for line in text.split("\n"):
        match = _HEADING.match(line)
        if match:
            current = []
            bodies.setdefault(match.group(1), []).append(current)
        elif current is not None:
            current.append(line)
    return {
        name: ["\n".join(raw).strip() for raw in raw_bodies]
        for name, raw_bodies in bodies.items()
    }


def _missing_unfilled(text: str) -> tuple[list[str], list[str]]:
    """The fields absent from *text* and those still unfilled, in form order."""

    bodies = _field_bodies(text)
    missing = [field for field in _FIELDS if field not in bodies]
    unfilled = [
        field
        for field in _FIELDS
        if field in bodies
        and any(body in ("", _placeholder(field)) for body in bodies[field])
    ]
    return missing, unfilled


def _scan_hits(
    safe_name: str, haystack: str, markers: tuple[str, ...]
) -> list[LeakHit]:
    """The hits one searched text produces under one masked file name.

    Signatures come from ``scan_for_leaks``; configured markers are
    identified by position exactly as ``scan_diff_for_leaks`` identifies
    them — ``private-marker #N`` — written once here so the two callers
    cannot drift.
    """

    hits = [LeakHit(safe_name, category) for category in scan_for_leaks(haystack)]
    hits.extend(
        LeakHit(safe_name, f"private-marker #{index}")
        for index, marker in enumerate(markers, start=1)
        if marker and marker in haystack
    )
    return hits


def _name_hits(name: str, markers: tuple[str, ...]) -> list[LeakHit]:
    """Scan one file name: it leaves with the batch, so it is content too.

    A name carrying a marker or matching a signature is a hit by itself,
    identified the way a content hit is — the masked name beside the
    marker's position or the signature's identifier.
    """

    return _scan_hits(_printable(name, markers), name, markers)


def _draft_hits(name: str, text: str, markers: tuple[str, ...]) -> list[LeakHit]:
    """Scan one draft — its name and its whole content.

    Every byte of a draft would be sent, so the whole text is scanned —
    the diff scan's added-lines rule does not carry over: its reason was
    not to re-flag what already sits in the tree, and a draft holds
    nothing else.
    """

    safe_name = _printable(name, markers)
    return _name_hits(name, markers) + _scan_hits(safe_name, text, markers)


def _is_regular(entry: Path) -> bool:
    """Whether *entry* is a regular file — not a symlink to one, not anything
    else; a failed stat is not a regular file either."""

    try:
        return not entry.is_symlink() and entry.is_file()
    except OSError:
        return False


class _CheckResult(NamedTuple):
    """What one check run leaves for its caller.

    ``status`` is the command's exit status; ``pinned`` maps each
    repository-relative outbox path's bytes to the blob id its checked
    content stages as, the sent manifest's entry naming the blob of the
    manifest's next content.
    ``drafts`` is one ``(sha256, shown name)`` pair per draft in outbox
    order — the line each earns in the manifest. ``manifest_old`` is the
    sent manifest's bytes as found — ``None`` when there is none — and
    ``manifest_new`` what it becomes once this batch sends.
    """

    status: int
    pinned: dict[bytes, bytes]
    drafts: list[tuple[str, str]]
    manifest_old: bytes | None
    manifest_new: bytes


def _manifest_next(
    manifest_lines: list[tuple[str, str]],
    drafts: list[tuple[str, str]],
    file_digests: dict[str, list[str]],
    present_names: set[str],
) -> bytes:
    """The manifest's content after this batch: its lines followed, plus
    one line per draft.

    A kept line holds its digest beside the name the file now carries:
    when the recorded name is gone from the outbox and the digest names
    exactly one file — a rename, a move inside the outbox — the line
    follows the new name, so the manifest still says where the sent file
    is. A line whose name still exists, or whose digest matches no file
    or several, is kept as written — the manifest is a record of what
    was sent. A kept line re-encodes to the very bytes it was read as —
    the strict parse accepted only UTF-8 in exactly ``<sha256>  <name>``
    form — so the rebuild normalizes exactly one thing: the final
    newline, which a manifest lacking it gains. Each draft's line is the
    sha256sum output form: digest, two spaces, the shown name.
    """

    lines = []
    for digest, name in manifest_lines:
        candidates = file_digests.get(digest, [])
        if name not in present_names and len(candidates) == 1:
            name = candidates[0]
        lines.append(f"{digest}  {name}\n")
    lines.extend(f"{digest}  {name}\n" for digest, name in drafts)
    return "".join(lines).encode()


def _run_check(index: Path | None, stderr: TextIO) -> int:
    return _check(stderr, index=index).status


def _check(stderr: TextIO, index: Path | None) -> _CheckResult:
    """The ``outbox check`` run: its status and what a send needs of it.

    A pin is the blob id the file stages as, computed by ``git
    hash-object --stdin --path`` from the very bytes this run read — the
    same clean filters the add applies, so the id is the one staging
    writes. The same bytes hashed ``--no-filters`` are the blob of what
    the scan saw: when the two ids differ, staging would commit content
    nobody checked and the file is refused rather than pinned
    (``_pinned_blob``) — the check's exit status is where a batch
    wrapper refuses before sending (ADR-0020 decision 3). Pinning at
    the read leaves no second read for an edit to slip through: a later
    send verifies it commits what was checked. The manifest is pinned
    once, the same way, on the manifest's next content — computed here,
    where the checked bytes are — so the update lands in the batch
    commit pinned like every file.
    """
    located = _locate("check", stderr)
    if located is None:
        return _CheckResult(1, {}, [], None, b"")
    project_root, outbox = located
    markers = _markers("check", project_root, stderr)
    if markers is None:
        return _CheckResult(1, {}, [], None, b"")

    # The sent manifest: one `<sha256>  <name>` line per file sent. Its
    # digests skip drafts; its names name a file whose bytes changed
    # since it was sent; its lines, in order, are what a send rewrites.
    # Anything but a readable regular file simply holds no digests — a
    # non-regular `SENT` is caught below like every non-regular entry.
    manifest_old: bytes | None = None
    manifest_lines: list[tuple[str, str]] = []
    manifest_names: set[str] = set()
    sent_digests: set[str] = set()
    sent_path = outbox / _SENT
    if _is_regular(sent_path):
        try:
            manifest_old = sent_path.read_bytes()
        except OSError as error:
            print(
                f"outbox check: cannot read the sent manifest: {_os_error_text(error)}",
                file=stderr,
            )
            return _CheckResult(1, {}, [], None, b"")
        # Strictly one entry per line, and strictly UTF-8 — a wrong
        # form, a name the record-text rules refuse, a carriage return,
        # a line that does not decode all fail to parse, and a malformed
        # line is never dropped in silence: each is named by number
        # before the refusal.
        raw_lines = manifest_old.split(b"\n")
        if raw_lines and raw_lines[-1] == b"":
            raw_lines.pop()
        malformed: list[int] = []
        for line_number, raw_line in enumerate(raw_lines, start=1):
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                malformed.append(line_number)
                continue
            match = _SENT_LINE.match(line)
            if match and not forges_rendered_text(match.group(2)):
                manifest_lines.append((match.group(1), match.group(2)))
                sent_digests.add(match.group(1))
                manifest_names.add(match.group(2))
            else:
                malformed.append(line_number)
        if malformed:
            for line_number in malformed:
                print(
                    f"{_printable(_SENT, markers)}: line {line_number} does not parse"
                )
            print("outbox check: refused", file=stderr)
            return _CheckResult(1, {}, [], manifest_old, b"")
    if index is not None:
        # The same parse `outbox status` runs on the same kind of file —
        # an index the operator obtained.
        try:
            sent_digests.update(_index_claims(index))
        except OSError as error:
            print(
                f"outbox check: cannot read the index "
                f"{_printable(index, markers)}: {_os_error_text(error)}",
                file=stderr,
            )
            return _CheckResult(1, {}, [], None, b"")

    try:
        entries = sorted(outbox.iterdir())
    except OSError as error:
        print(
            f"outbox check: cannot read the outbox at "
            f"{_printable(outbox, markers)}: {_os_error_text(error)}",
            file=stderr,
        )
        return _CheckResult(1, {}, [], None, b"")

    refused = False
    checked = 0
    skipped = 0
    pinned: dict[bytes, bytes] = {}
    drafts: list[tuple[str, str]] = []
    hits: list[LeakHit] = []
    file_digests: dict[str, list[str]] = {}
    present_names: set[str] = set()
    for entry in entries:
        # The escaped printable form of the name — a surrogate-carrying
        # non-UTF-8 name used to crash the prints below (CR-156's carried
        # advisory); this form is also what the name scan and the
        # manifest's name matching see. `_printable` masks it first and
        # escapes second, so a secret beside a control character is still
        # masked and nothing printed can carry a line-forging character.
        name = _shown_name(entry.name)
        if not _is_regular(entry):
            # Not a draft and not checkable, but a later send would stage
            # it unchecked — nothing in the outbox passes in silence.
            refused = True
            hits.extend(_name_hits(name, markers))
            print(f"{_printable(entry.name, markers)}: not a draft, not checked")
            continue
        # The README init writes and the manifest send writes are not
        # drafts; a file whose sha256 a manifest line — or a `Source:`
        # line of the passed index — lists is already sent, not a draft
        # either. All of them still leave with the batch, so their names
        # and contents go through the same scan.
        is_draft = entry.name != _README and entry.name != _SENT
        if entry.name != _SENT:
            present_names.add(name)
        problems: list[str] = []
        notes: list[str] = []
        # A manifest line is one line — a name that could add one is
        # never written there. The escaped display form names it.
        if forges_rendered_text(name):
            problems.append("a name that could add a line to the sent manifest")
        text = ""
        try:
            raw = entry.read_bytes()
        except OSError as error:
            problems.append(f"cannot be read: {_os_error_text(error)}")
        else:
            digest = hashlib.sha256(raw).hexdigest()
            if entry.name != _SENT:
                file_digests.setdefault(digest, []).append(name)
            if is_draft and digest in sent_digests:
                skipped += 1
                is_draft = False
            elif is_draft and name in manifest_names:
                notes.append("changed after sending")
            if is_draft:
                checked += 1
                drafts.append((digest, name))
            if entry.name != _SENT:
                # The key is the repository-relative path's real bytes —
                # the form `ls-files` reports — so a non-UTF-8 name is
                # pinned without ever becoming text. `SENT` is pinned
                # once below, on the content send writes — not on the
                # bytes it found.
                relative = f"{_OUTBOX_PREFIX}{entry.name}"
                try:
                    pinned_blob = _pinned_blob(project_root, relative, raw)
                except _OutboxGitError as error:
                    problems.append(
                        f"cannot be pinned: {safe_path(str(error), markers)}"
                    )
                else:
                    if pinned_blob is None:
                        problems.append(
                            "git would transform it on staging — "
                            + _transform_cause(project_root, relative)
                        )
                    else:
                        pinned[os.fsencode(relative)] = pinned_blob
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                # The lossy-search rule the diff scan follows: undecodable
                # spans become U+FFFD, a non-word character, so an ASCII
                # signature or marker beside them still matches.
                text = raw.decode("utf-8", errors="replace")
                if is_draft:
                    problems.append("not UTF-8 text")
            else:
                if is_draft:
                    missing, unfilled = _missing_unfilled(text)
                    if missing:
                        problems.append("missing " + ", ".join(missing))
                    if unfilled:
                        problems.append("unfilled " + ", ".join(unfilled))
        hits.extend(_draft_hits(name, text, markers))
        if problems:
            refused = True
        report = problems + notes
        if report:
            print(f"{_printable(entry.name, markers)}: {'; '.join(report)}")
    # The manifest's next content is computed even when nothing pins it —
    # a check that passes hands send the exact bytes to write. Those
    # bytes are staged like every file, so the scan covers them too: a
    # name that trips nothing alone can match once it sits on a manifest
    # line — a signature whose match spans the line break.
    manifest_new = _manifest_next(manifest_lines, drafts, file_digests, present_names)
    hits.extend(
        _scan_hits(
            safe_path(_SENT, markers),
            manifest_new.decode("utf-8", errors="replace"),
            markers,
        )
    )
    # The manifest's one pin is the blob of the content send writes —
    # not of the bytes it found. A manifest that does not exist and has
    # nothing to record stages nothing, so it takes no pin either. It is
    # held to the same checked-bytes rule as every file: a filter that
    # would rewrite it on staging refuses the run.
    if manifest_old is not None or manifest_new:
        relative = f"{_OUTBOX_PREFIX}{_SENT}"
        try:
            manifest_blob = _pinned_blob(project_root, relative, manifest_new)
        except _OutboxGitError as error:
            refused = True
            print(
                f"{_printable(_SENT, markers)}: cannot be pinned: "
                f"{safe_path(str(error), markers)}"
            )
        else:
            if manifest_blob is None:
                refused = True
                print(
                    f"{_printable(_SENT, markers)}: git would transform it "
                    f"on staging — {_transform_cause(project_root, relative)}"
                )
            else:
                pinned[os.fsencode(relative)] = manifest_blob
    if skipped:
        print(f"skipped as sent: {skipped}")
    if hits:
        refused = True
        print(
            "outbox check: possible leaks in drafts (file: what matched): "
            + render_leak_hits(sorted(set(hits)), limit=None)
        )
        print(
            "(best-effort: a hit is not proof of a leak and a clean run is "
            "not proof of safety — see ADR-0005)",
            file=stderr,
        )
    if refused:
        print("outbox check: refused", file=stderr)
        return _CheckResult(1, pinned, drafts, manifest_old, manifest_new)
    print(
        f"outbox check: {checked} draft(s) checked; all conform; "
        "no known leak signatures"
    )
    return _CheckResult(0, pinned, drafts, manifest_old, manifest_new)


# --- `outbox send` ---------------------------------------------------------


class _OutboxGitError(Exception):
    """A git invocation for the outbox failed or could not be run."""


def _git(project_root: Path, arguments: list[str], feed: bytes = b"") -> bytes:
    """Run git in the project repository and return stdout bytes.

    Mirrors ``gate``'s ``_run_git_bytes``: a missing git is described by
    its errno text — never ``str(OSError)``, which carries a path — and a
    non-zero exit by git's own stderr decoded lossily. The error names
    only the subcommand: the arguments stay out of it because one of them
    can be the whole commit message. A path git quotes back can itself
    carry a marker, so the caller prints the message masked. *feed* is
    piped to git's stdin — the plumbing ``send`` uses to put index
    entries back takes its records there.
    """

    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            check=False,
            input=feed,
        )
    except OSError as error:
        raise _OutboxGitError(f"cannot run git: {_os_error_text(error)}") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="backslashreplace").strip()
        raise _OutboxGitError(
            f"git {arguments[0]} failed" + (f": {detail}" if detail else "")
        )
    return result.stdout


def _pinned_blob(project_root: Path, relative: str, content: bytes) -> bytes | None:
    """The blob id *content* stages as at *relative* — or ``None``.

    ``--path`` applies the attributes the ``add`` will apply, so the id
    is the one staging writes; ``--no-filters`` is the blob of the bytes
    exactly as the check read them. A difference means a clean filter or
    an end-of-line conversion would commit content the check never saw —
    the caller refuses the file instead of pinning it, so only checked
    bytes are ever committed.
    """

    staged = _git(
        project_root,
        ["hash-object", "--stdin", f"--path={relative}"],
        content,
    ).strip()
    plain = _git(
        project_root, ["hash-object", "--stdin", "--no-filters"], content
    ).strip()
    return staged if staged == plain else None


def _autocrlf(project_root: Path) -> bool:
    """Whether ``core.autocrlf`` is set to a value that converts.

    Asked of git with its own ``--type=bool-or-str`` read, so every
    spelling git takes for true — ``yes``, ``on``, ``1``, the key
    without a value — lands as ``true`` beside the literal, and
    ``input`` converts as well; ``false``'s spellings, an unset key —
    ``config --get`` exits non-zero on it — and a value that is no
    spelling of either do not.
    """

    try:
        value = (
            _git(
                project_root,
                ["config", "--type=bool-or-str", "--get", "core.autocrlf"],
            )
            .decode("ascii", errors="replace")
            .strip()
        )
    except _OutboxGitError:
        return False
    return value in ("true", "input")


def _transform_cause(project_root: Path, relative: str) -> str:
    """Why git would rewrite the checked bytes on staging, and the remedy.

    The attributes applying at *relative* name the conversion the
    mismatched blob id came from: a set ``filter`` is a clean filter —
    refused with the rule that it must not apply to the outbox. For
    end-of-line conversion the attributes speak first: ``text`` or
    ``eol`` applying is conversion, ``-text`` turns normalisation off
    for good — neither ``eol`` nor ``core.autocrlf`` re-enables it —
    and only where no attribute speaks does ``core.autocrlf`` decide,
    so the ``-text`` remedy is named only where it would change
    anything. Anything else — an encoding conversion, say — is refused
    without a named remedy, exactly as before.
    """

    attributes: dict[str, str] = {}
    try:
        out = _git(
            project_root,
            ["check-attr", "-z", "filter", "text", "eol", "--", relative],
        )
    except _OutboxGitError:
        out = b""
    fields = out.split(b"\0")
    for index in range(0, len(fields) - len(fields) % 3, 3):
        attributes[fields[index + 1].decode("utf-8", "backslashreplace")] = fields[
            index + 2
        ].decode("utf-8", "backslashreplace")
    causes: list[str] = []
    if attributes.get("filter", "unspecified") not in ("unspecified", "unset"):
        causes.append(
            "a clean filter applies — the filter must not apply to the outbox"
        )
    text = attributes.get("text", "unspecified")
    eol = attributes.get("eol", "unspecified")
    if text != "unset" and (
        text != "unspecified"
        or eol not in ("unspecified", "unset")
        or _autocrlf(project_root)
    ):
        causes.append(
            "end-of-line conversion applies — "
            f"`{_OUTBOX_DIR_SPEC}/** -text` in .gitattributes (or committing "
            "the file with the bytes git stages) makes the bytes match"
        )
    if not causes:
        causes.append("a clean filter or eol conversion applies")
    return "; ".join(causes)


def _staged_name_status(project_root: Path) -> list[tuple[str, list[str]]]:
    """The staged changes as ``(status, paths)`` pairs, renames detected.

    ``git diff --cached`` reads an unborn-HEAD repository against the
    empty tree, so a first send needs no special case. ``-M`` reports a
    staged rename as one entry carrying both its paths — the form the
    batch's committable test needs, since a change to a file already
    sent can be a rename whose add half alone reads as new. ``-z``
    keeps names as bytes; each is decoded to the escaped printable
    form — a non-UTF-8 path can be staged as easily as created.
    """

    raw = _git(project_root, ["diff", "--cached", "--name-status", "-z", "-M"])
    tokens = [token for token in raw.split(b"\0") if token]
    entries: list[tuple[str, list[str]]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].decode("ascii", errors="replace")[0]
        if status in "RC":
            if index + 2 >= len(tokens):
                raise _OutboxGitError("unparseable rename in the staged list")
            entries.append(
                (
                    status,
                    [_shown_name(tokens[index + 1]), _shown_name(tokens[index + 2])],
                )
            )
            index += 3
        else:
            if index + 1 >= len(tokens):
                raise _OutboxGitError("unparseable entry in the staged list")
            entries.append((status, [_shown_name(tokens[index + 1])]))
            index += 2
    return entries


def _staged_paths(project_root: Path) -> set[str]:
    """Every path the index's difference from HEAD names.

    A rename or copy contributes both its paths because either can be
    the one outside the outbox.
    """

    paths: set[str] = set()
    for _, names in _staged_name_status(project_root):
        paths.update(names)
    return paths


def _restore_outbox_index(project_root: Path, records: bytes) -> str | None:
    """Un-stage exactly what a refused send staged under the outbox.

    *records* is the ``git ls-files --stage -z`` output taken before the
    batch was staged. Replaying it through ``update-index --index-info``
    puts every recorded entry back — including one the add rewrote —
    while ``--force-remove`` drops each path now staged under the outbox
    that no record names: the additions the send made. Neither step
    writes an object id, so the repository's object format cannot break
    it — a mode-0 index-info line would have to name the format's null
    id — and the plumbing form works where ``restore --staged`` cannot,
    an unborn HEAD. Nothing outside the outbox is ever in either list. A
    failure is returned as text for the caller to warn about; the refusal
    stands either way.
    """

    try:
        current = _git(project_root, ["ls-files", "-z", "--", _OUTBOX_DIR_SPEC])
        recorded = {
            token.split(b"\t", 1)[1] for token in records.split(b"\0") if b"\t" in token
        }
        additions = b"".join(
            path + b"\0"
            for path in current.split(b"\0")
            if path and path not in recorded
        )
        if additions:
            _git(
                project_root,
                ["update-index", "--force-remove", "-z", "--stdin"],
                additions,
            )
        if records:
            _git(project_root, ["update-index", "-z", "--index-info"], records)
    except _OutboxGitError as error:
        return str(error)
    return None


def _batch_mismatch(
    project_root: Path, expected: dict[bytes, bytes], markers: tuple[str, ...]
) -> list[str]:
    """The outbox names whose staged blob is not what the check saw.

    Every pinned path must sit in the index at stage 0 with exactly the
    pinned blob id, and nothing else may be staged under the outbox: a
    file that arrived after the check was never vetted, and a changed or
    removed one would commit content nobody checked. The names come back
    masked and display-escaped — the caller prints them inside the
    refusal.
    """

    raw = _git(project_root, ["ls-files", "--stage", "-z", "--", _OUTBOX_DIR_SPEC])
    staged: dict[bytes, list[tuple[bytes, bytes]]] = {}
    for token in raw.split(b"\0"):
        if not token:
            continue
        meta, separator, path = token.partition(b"\t")
        fields = meta.split(b" ")
        if not separator or len(fields) != 3:
            raise _OutboxGitError("unparseable index record")
        staged.setdefault(path, []).append((fields[1], fields[2]))
    bad = [
        path for path, blob in expected.items() if staged.get(path) != [(blob, b"0")]
    ]
    bad.extend(path for path in staged if path not in expected)
    return sorted(_printable(path, markers) for path in bad)


def _restore_manifest(sent_path: Path, manifest_old: bytes | None) -> str | None:
    """Put the sent manifest back as a refused send found it.

    *manifest_old* is the manifest's bytes as found — ``None`` when
    there was none, so the file the send wrote is removed. A failure is
    returned as text for the caller to warn about; the refusal stands
    either way.
    """

    try:
        if manifest_old is None:
            sent_path.unlink(missing_ok=True)
        else:
            sent_path.write_bytes(manifest_old)
    except OSError as error:
        return f"could not restore the sent manifest: {_os_error_text(error)}"
    return None


def _run_send(index: Path | None, stderr: TextIO) -> int:
    # The check runs literally: its report is the operator's reason, and
    # any refusal it voices refuses the send. The pins it brings back are
    # the blob ids of the very bytes it read — the manifest's update
    # pinned like every file — what the commit must show.
    result = _check(stderr, index=index)
    if result.status != 0:
        print("outbox send: refused — the check did not pass", file=stderr)
        return 1
    located = _locate("send", stderr)
    if located is None:
        return 1
    project_root, outbox = located
    markers = _markers("send", project_root, stderr)
    if markers is None:
        return 1
    try:
        staged = _staged_paths(project_root)
    except _OutboxGitError as error:
        print(f"outbox send: {safe_path(str(error), markers)}", file=stderr)
        return 1
    outside = sorted(path for path in staged if not path.startswith(_OUTBOX_PREFIX))
    if outside:
        # Findings must not ride along in another commit, nor another
        # commit's work in the batch — the staged set outside the outbox
        # is the operator's to commit or unstage first.
        print(
            "outbox send: staged outside the outbox — commit or unstage it "
            "first: " + ", ".join(_printable(path, markers) for path in outside),
            file=stderr,
        )
        return 1
    sent_path = outbox / _SENT
    sent_spec = f"{_OUTBOX_PREFIX}{_SENT}"
    index_records: bytes | None = None
    committed = False
    try:
        # Taken before the manifest write and the add so a refused send
        # can put the index — and the manifest's bytes — back exactly as
        # it found them under the outbox.
        index_records = _git(
            project_root, ["ls-files", "--stage", "-z", "--", _OUTBOX_DIR_SPEC]
        )
        # The manifest the check computed lands before the add — when it
        # moved — so the batch commit carries it pinned like every file.
        if result.manifest_new != (result.manifest_old or b""):
            try:
                sent_path.write_bytes(result.manifest_new)
            except OSError as error:
                raise _OutboxGitError(
                    f"cannot write the sent manifest: {_os_error_text(error)}"
                ) from error
        # --force: an ignore rule must not silently drop a draft the check
        # just passed — the whole outbox is what leaves.
        _git(project_root, ["add", "--force", "--", _OUTBOX_DIR_SPEC])
        batch_entries = [
            (status, names)
            for status, names in _staged_name_status(project_root)
            if any(name.startswith(_OUTBOX_PREFIX) for name in names)
        ]
        batch = sorted(name for _, names in batch_entries for name in names)
        if not result.drafts:
            # No finding draft is no finding batch — unless the only
            # changes the outbox holds are renames or moves of files
            # already sent (staged `R` entries) and the manifest update
            # that follows one: a change to a file already sent is the
            # outbox's own commit (ADR-0020 decision 6: the exclude
            # pathspec keeps findings out of journal commits). A passed
            # check that found no draft leaves a regular file no other
            # change to make — the README and the manifest are never
            # drafts and every other file is already sent — so anything
            # else staged, a modified README, an addition, a deletion,
            # or the manifest alone, refuses as no drafts, exactly as
            # before.
            if not any(status == "R" for status, _ in batch_entries) or any(
                status != "R" and names != [sent_spec]
                for status, names in batch_entries
            ):
                raise _OutboxGitError("no drafts to send")
        elif not batch or batch == [sent_spec]:
            # The manifest update alone is no batch: when every draft is
            # committed and unchanged there is nothing to send.
            raise _OutboxGitError(
                "nothing to send — the outbox has no uncommitted changes"
            )
        changed = _batch_mismatch(project_root, result.pinned, markers)
        if changed:
            raise _OutboxGitError("changed since the check: " + ", ".join(changed))
        message = "outbox: findings batch\n\n" + "\n".join(
            f"- {escape_for_display(path)}" for path in batch
        )
        _git(project_root, ["commit", "--message", message])
        committed = True
    except _OutboxGitError as error:
        # The refusal stands, but whatever the send staged must not stay:
        # the index goes back to what the send found, and the manifest's
        # bytes with it — a failed commit never leaves a manifest
        # claiming files it did not land. Only a refusal touches either —
        # a made commit is never rolled back.
        if index_records is not None and not committed:
            restore_error = _restore_outbox_index(project_root, index_records)
            if restore_error is not None:
                print(
                    f"outbox send: could not restore the index: "
                    f"{safe_path(restore_error, markers)}",
                    file=stderr,
                )
            manifest_error = _restore_manifest(sent_path, result.manifest_old)
            if manifest_error is not None:
                print(
                    f"outbox send: {safe_path(manifest_error, markers)}",
                    file=stderr,
                )
        print(f"outbox send: {safe_path(str(error), markers)}", file=stderr)
        return 1
    try:
        commit = _git(project_root, ["rev-parse", "HEAD"]).decode("ascii").strip()
    except _OutboxGitError as error:
        print(
            f"outbox send: the batch is committed but its id could not be "
            f"read: {safe_path(str(error), markers)}",
            file=stderr,
        )
        return 1
    print(commit)
    return 0


# --- `outbox status` -------------------------------------------------------


# One index entry: `Source:` — optionally `**`-decorated the way a
# published digest header writes it — followed by whitespace, an optional
# backtick, `sha256:` and 64 hexadecimal digits, then an optional closing
# backtick. Each occurrence is an entry, identified by its digest — the
# line it sits on is kept for the report, and a digest carried by two
# lines is still one entry.
_SOURCE_LINE = re.compile(r"(?:\*\*Source:\*\*|Source:)\s*`?sha256:([0-9A-Fa-f]{64})`?")


def _index_claims(index_path: Path) -> dict[str, list[int]]:
    """The index's ``Source:`` digests mapped to the lines they sit on.

    The parse ``status`` reports from is the one ``check`` and ``send``
    skip by — kept in one place so the commands cannot drift. The
    ``OSError`` of an unreadable index is the caller's to describe: each
    command names the file the way it names files.
    """

    index_text = index_path.read_bytes().decode("utf-8", errors="replace")
    by_digest: dict[str, list[int]] = {}
    for line_number, line in enumerate(index_text.split("\n"), start=1):
        for match in _SOURCE_LINE.finditer(line):
            claim_lines = by_digest.setdefault(match.group(1).lower(), [])
            if line_number not in claim_lines:
                claim_lines.append(line_number)
    return by_digest


def _run_status(index_path: Path, stderr: TextIO) -> int:
    located = _locate("status", stderr)
    if located is None:
        return 1
    project_root, outbox = located
    markers = _markers("status", project_root, stderr)
    if markers is None:
        return 1
    try:
        by_digest = _index_claims(index_path)
    except OSError as error:
        print(
            f"outbox status: cannot read the index "
            f"{_printable(index_path, markers)}: "
            f"{_os_error_text(error)}",
            file=stderr,
        )
        return 1
    try:
        entries = sorted(outbox.iterdir())
    except OSError as error:
        print(
            f"outbox status: cannot read the outbox at "
            f"{_printable(outbox, markers)}: {_os_error_text(error)}",
            file=stderr,
        )
        return 1

    refused = False
    claimed: set[str] = set()
    for entry in entries:
        name = _printable(entry.name, markers)
        if not _is_regular(entry):
            # Not a file and not hashable — the check's "nothing passes in
            # silence" rule, applied to the channel's other direction.
            refused = True
            print(f"{name}: not a regular file, not hashed")
            continue
        try:
            raw = entry.read_bytes()
        except OSError as error:
            refused = True
            print(f"{name}: cannot be read: {_os_error_text(error)}")
            continue
        digest = hashlib.sha256(raw).hexdigest()
        lines = by_digest.get(digest)
        if lines:
            claimed.add(digest)
            plural = "s" if len(lines) > 1 else ""
            print(f"{name}: claimed by index line{plural} {', '.join(map(str, lines))}")
        else:
            print(f"{name}: no index entry")
    for digest, lines in by_digest.items():
        if digest not in claimed:
            plural = "s" if len(lines) > 1 else ""
            print(
                f"index line{plural} {', '.join(map(str, lines))}: "
                f"sha256:{digest} claims no outbox file"
            )
    if refused:
        print("outbox status: refused", file=stderr)
        return 1
    return 0
