"""The ``outbox`` command group: finding drafts for upstream.

ADR-0020 decisions 1-5: one command group named ``outbox`` covers the life
of a finding for upstream; ``finding`` stays the journal command of
ADR-0009. ``outbox new`` scaffolds a draft carrying the five fields of
CONTRIBUTING's finding form, Version and Environment filled from the
machine. ``outbox check`` names, per draft, the file and each missing or
still-unfilled field, runs the merge boundary's leak scan over what would
be sent, and refuses by exit status so a batch wrapper can refuse to send.
``outbox send`` runs that check, stages only the outbox and makes one
batch commit — delivery stays with the operator. ``outbox status`` hashes
the outbox files and compares them with the ``Source:`` lines of an index
file the operator passes. The group opens no network.

The outbox is ``project_root/.agentmarshal/upstream`` — the directory
``init`` scaffolds beside ``project.json`` — which is the same expression
in both placements: in an embedded project it is the host repository's
``.agentmarshal``, in a sidecar the journal repository's, so a batch
commit lands in the journal repository and never touches the host.
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
from typing import TextIO

from agentmarshal import __version__
from agentmarshal.journal.capture import (
    CaptureError,
    LeakHit,
    render_leak_hits,
    safe_path,
    scan_for_leaks,
)
from agentmarshal.journal.gate import GateError, markers_from_config
from agentmarshal.project import PROJECT_DIR_NAME, find_project_root

_UPSTREAM_DIR = "upstream"
_README = "README.md"
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
    outbox_commands.add_parser(
        "check", help="name what the drafts lack and what the leak scan finds"
    )
    outbox_commands.add_parser(
        "send", help="check, then commit the outbox as one batch"
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
        return _run_check(stderr)
    if args.outbox_command == "send":
        return _run_send(stderr)
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

    return _scan_hits(safe_path(name, markers), name, markers)


def _draft_hits(name: str, text: str, markers: tuple[str, ...]) -> list[LeakHit]:
    """Scan one draft — its name and its whole content.

    Every byte of a draft would be sent, so the whole text is scanned —
    the diff scan's added-lines rule does not carry over: its reason was
    not to re-flag what already sits in the tree, and a draft holds
    nothing else.
    """

    safe_name = safe_path(name, markers)
    return _name_hits(name, markers) + _scan_hits(safe_name, text, markers)


def _is_regular(entry: Path) -> bool:
    """Whether *entry* is a regular file — not a symlink to one, not anything
    else; a failed stat is not a regular file either."""

    try:
        return not entry.is_symlink() and entry.is_file()
    except OSError:
        return False


def _run_check(stderr: TextIO) -> int:
    located = _locate("check", stderr)
    if located is None:
        return 1
    project_root, outbox = located
    markers = _markers("check", project_root, stderr)
    if markers is None:
        return 1
    try:
        entries = sorted(outbox.iterdir())
    except OSError as error:
        print(
            f"outbox check: cannot read the outbox at "
            f"{safe_path(_shown_name(outbox), markers)}: {_os_error_text(error)}",
            file=stderr,
        )
        return 1

    refused = False
    checked = 0
    hits: list[LeakHit] = []
    for entry in entries:
        # The escaped printable form of the name — a surrogate-carrying
        # non-UTF-8 name used to crash the print below (CR-156's carried
        # advisory); this form is also what the name scan and the masking
        # see.
        name = _shown_name(entry.name)
        if not _is_regular(entry):
            # Not a draft and not checkable, but a later send would stage
            # it unchecked — nothing in the outbox passes in silence.
            refused = True
            hits.extend(_name_hits(name, markers))
            print(f"{safe_path(name, markers)}: not a draft, not checked")
            continue
        # The README init writes is not a draft — the field check below
        # skips it — but it leaves with the batch like every file, so its
        # name and content go through the same scan.
        is_draft = entry.name != _README
        if is_draft:
            checked += 1
        problems: list[str] = []
        text = ""
        try:
            raw = entry.read_bytes()
        except OSError as error:
            problems.append(f"cannot be read: {_os_error_text(error)}")
        else:
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
            print(f"{safe_path(name, markers)}: {'; '.join(problems)}")
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
        return 1
    print(
        f"outbox check: {checked} draft(s) checked; all conform; "
        "no known leak signatures"
    )
    return 0


# --- `outbox send` ---------------------------------------------------------


class _OutboxGitError(Exception):
    """A git invocation for the outbox failed or could not be run."""


def _git(project_root: Path, arguments: list[str], feed: bytes = b"") -> bytes:
    """Run git in the project repository and return stdout bytes.

    Mirrors ``gate``'s ``_run_git_bytes``: a missing git is described by
    its errno text — never ``str(OSError)``, which carries a path — and a
    non-zero exit by git's own stderr decoded lossily. A path git quotes
    back can itself carry a marker, so the caller prints the message
    masked. *feed* is piped to git's stdin — the plumbing ``send`` uses
    to put index entries back takes its records there.
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
            f"git {' '.join(arguments)} failed" + (f": {detail}" if detail else "")
        )
    return result.stdout


def _staged_paths(project_root: Path) -> list[tuple[str, str, str | None]]:
    """The index's difference from HEAD as ``(status, path, source)``.

    ``git diff --cached`` reads an unborn-HEAD repository against the
    empty tree, so a first send needs no special case. ``-z`` keeps names
    as bytes; each is decoded to the escaped printable form — a non-UTF-8
    path can be staged as easily as created. A rename or copy contributes
    both its paths, destination first, because either can be the one
    outside the outbox.
    """

    raw = _git(project_root, ["diff", "--cached", "--name-status", "-z"])
    tokens = [token for token in raw.split(b"\0") if token]
    entries: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].decode("ascii", errors="replace")[0]
        if status in "RC":
            if index + 2 >= len(tokens):
                raise _OutboxGitError("unparseable rename in the staged list")
            entries.append(
                (status, _shown_name(tokens[index + 2]), _shown_name(tokens[index + 1]))
            )
            index += 3
        else:
            if index + 1 >= len(tokens):
                raise _OutboxGitError("unparseable entry in the staged list")
            entries.append((status, _shown_name(tokens[index + 1]), None))
            index += 2
    return entries


def _restore_outbox_index(project_root: Path, records: bytes) -> str | None:
    """Un-stage exactly what a refused send staged under the outbox.

    *records* is the ``git ls-files --stage -z`` output taken before the
    batch was staged. Replaying it through ``update-index --index-info``
    puts every recorded entry back — including one the add rewrote —
    while a mode-0 line drops each path now staged under the outbox that
    no record names: the additions the send made. Nothing outside the
    outbox is ever in either list, and the plumbing form works where
    ``restore --staged`` cannot — an unborn HEAD. A failure is returned
    as text for the caller to warn about; the refusal stands either way.
    """

    try:
        current = _git(project_root, ["ls-files", "-z", "--", _OUTBOX_DIR_SPEC])
        recorded = {
            token.split(b"\t", 1)[1] for token in records.split(b"\0") if b"\t" in token
        }
        removals = b"".join(
            b"0 " + b"0" * 40 + b"\t" + path + b"\0"
            for path in current.split(b"\0")
            if path and path not in recorded
        )
        _git(project_root, ["update-index", "-z", "--index-info"], records + removals)
    except _OutboxGitError as error:
        return str(error)
    return None


def _run_send(stderr: TextIO) -> int:
    # The check runs literally: its report is the operator's reason, and
    # any refusal it voices refuses the send.
    if _run_check(stderr) != 0:
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
        # The check just passed, so every entry is a regular file and a
        # draft is any name but the README init writes — a batch of no
        # drafts would commit the README alone.
        if not any(entry.name != _README for entry in outbox.iterdir()):
            print("outbox send: no drafts to send", file=stderr)
            return 1
    except OSError as error:
        print(
            f"outbox send: cannot read the outbox at "
            f"{safe_path(_shown_name(outbox), markers)}: {_os_error_text(error)}",
            file=stderr,
        )
        return 1
    try:
        staged = _staged_paths(project_root)
    except _OutboxGitError as error:
        print(f"outbox send: {safe_path(str(error), markers)}", file=stderr)
        return 1
    outside = sorted(
        {
            staged_path
            for _, path, source in staged
            for staged_path in (path, source)
            if staged_path is not None and not staged_path.startswith(_OUTBOX_PREFIX)
        }
    )
    if outside:
        # Findings must not ride along in another commit, nor another
        # commit's work in the batch — the staged set outside the outbox
        # is the operator's to commit or unstage first.
        print(
            "outbox send: staged outside the outbox — commit or unstage it "
            "first: " + ", ".join(safe_path(path, markers) for path in outside),
            file=stderr,
        )
        return 1
    index_records: bytes | None = None
    try:
        # Taken before the add so a refused send can put the index back
        # exactly as it found it under the outbox.
        index_records = _git(
            project_root, ["ls-files", "--stage", "-z", "--", _OUTBOX_DIR_SPEC]
        )
        # --force: an ignore rule must not silently drop a draft the check
        # just passed — the whole outbox is what leaves.
        _git(project_root, ["add", "--force", "--", _OUTBOX_DIR_SPEC])
        batch = sorted(
            {
                staged_path
                for _, path, source in _staged_paths(project_root)
                for staged_path in (path, source)
                if staged_path is not None and staged_path.startswith(_OUTBOX_PREFIX)
            }
        )
        if not batch:
            raise _OutboxGitError(
                "nothing to send — the outbox has no uncommitted changes"
            )
        message = "outbox: findings batch\n\n" + "\n".join(
            f"- {path}" for path in batch
        )
        _git(project_root, ["commit", "--message", message])
        commit = _git(project_root, ["rev-parse", "HEAD"]).decode("ascii").strip()
    except _OutboxGitError as error:
        # The refusal stands, but a failed commit must not leave behind
        # the batch the add already staged.
        if index_records is not None:
            restore_error = _restore_outbox_index(project_root, index_records)
            if restore_error is not None:
                print(
                    f"outbox send: could not restore the index: "
                    f"{safe_path(restore_error, markers)}",
                    file=stderr,
                )
        print(f"outbox send: {safe_path(str(error), markers)}", file=stderr)
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


def _run_status(index_path: Path, stderr: TextIO) -> int:
    located = _locate("status", stderr)
    if located is None:
        return 1
    project_root, outbox = located
    markers = _markers("status", project_root, stderr)
    if markers is None:
        return 1
    try:
        index_text = index_path.read_bytes().decode("utf-8", errors="replace")
    except OSError as error:
        print(
            f"outbox status: cannot read the index "
            f"{safe_path(_shown_name(index_path), markers)}: "
            f"{_os_error_text(error)}",
            file=stderr,
        )
        return 1
    by_digest: dict[str, list[int]] = {}
    for line_number, line in enumerate(index_text.split("\n"), start=1):
        for match in _SOURCE_LINE.finditer(line):
            claim_lines = by_digest.setdefault(match.group(1).lower(), [])
            if line_number not in claim_lines:
                claim_lines.append(line_number)
    try:
        entries = sorted(outbox.iterdir())
    except OSError as error:
        print(
            f"outbox status: cannot read the outbox at "
            f"{safe_path(_shown_name(outbox), markers)}: {_os_error_text(error)}",
            file=stderr,
        )
        return 1

    refused = False
    claimed: set[str] = set()
    for entry in entries:
        name = safe_path(_shown_name(entry.name), markers)
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
