"""The ``extension`` command group: local run grants for shared extensions.

ADR-0013 decision 14: a local grant covers the hash of the whole extension
directory — the manifest, ``bin/``, the lock — kept by ``agentmarshal
extension trust | untrust | list``. ADR-0014's map places ``trust.toml`` in
the clone's local state; ADR-0022 section 7 fixes the file's shape — a name
to the directory hash granted, who granted it and when — and names the
``trust-changed`` process-log event. The file also keeps each file's own
hash so ``list`` can name what changed.

``trust`` hashes every regular file under
``.agentmarshal/extensions/<name>/`` of the journal repository's working
tree and records one grant; ``untrust`` removes it; ``list`` recomputes
the hashes and reports each directory-form extension's state — granted,
not granted, or changed after approval naming the first differing file.
Decision 15's bound stands: this guards against accidental change and a
sandboxed executor, not a process running with the user's rights — nothing
here locks the file or checks ownership. No command runs an extension and
none writes the journal.

The ``switch`` group — ``extension switch off <name> --reason <text>``,
the operational switch-off of decisions 16 and 17 — is registered here
under the same ``extension`` group; its logic lives in ``switch_off.py``.

``extension disable <name>`` and ``extension enable <name>`` are the
personal switch of decision 11: they write and clear a ``state = "off"``
entry under ``[switches.<name>]`` in the clone's ``switches.toml``
(``LocalState.switches_file``) for a personal extension — one declared
under the clone's ``LocalState.extensions`` — and refuse a name any
shared extension declares, which an operational task alone may switch.
``disable`` takes an optional ``--reason`` under the shared field's rule.
``read_personal_manifest`` is the clone-side manifest reader both they
and ``doctor`` use.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import tomllib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from agentmarshal.journal.actors import resolve_recorded_by
from agentmarshal.journal.contracts import (
    JournalContractError,
    reject_control_characters,
)
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    ExtensionManifest,
    ExtensionManifestError,
    _manifest_directory_paths,
    _require_existing_directory_file,
    _validate_name,
    parse_extension_manifest_text,
)
from agentmarshal.journal.placement import (
    Placement,
    PlacementError,
    resolve_placement,
)
from agentmarshal.localstate import LocalState, LocalStateError, local_state
from agentmarshal.process_log import ProcessLogError, open_writer, write_event
from agentmarshal.project import find_project_root
from agentmarshal.switches import (
    REASON_CHAR_LIMIT,
    PersonalSwitch,
    SwitchesError,
    personal_extension_names,
    read_personal_switches,
    shared_extension_names,
)

TRUST_FORMAT = 1

_TOML_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


class ExtensionTrustError(Exception):
    """Raised when a grant cannot be computed, read or written."""


@dataclass(frozen=True)
class Grant:
    """One extension's recorded grant: the approved contents and who."""

    directory_hash: str
    granted_by: str
    granted_by_source: str
    granted_at: str
    files: dict[str, str]


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``extension`` group and its subcommands to *subparsers*."""

    extension_parser = subparsers.add_parser(
        "extension", help="keep local run grants for shared extensions"
    )
    extension_commands = extension_parser.add_subparsers(
        dest="extension_command", required=True
    )
    trust_parser = extension_commands.add_parser(
        "trust", help="grant this clone's approval of an extension's contents"
    )
    trust_parser.add_argument("name", help="extension name")
    untrust_parser = extension_commands.add_parser(
        "untrust", help="withdraw this clone's grant"
    )
    untrust_parser.add_argument("name", help="extension name")
    extension_commands.add_parser(
        "list", help="show each directory-form extension's grant state"
    )
    switch_parser = extension_commands.add_parser(
        "switch",
        help="switch a shared extension off through an operational task",
    )
    switch_commands = switch_parser.add_subparsers(dest="switch_command", required=True)
    off_parser = switch_commands.add_parser(
        "off", help="open an operational task switching the extension off"
    )
    off_parser.add_argument("name", help="extension name")
    off_parser.add_argument(
        "--reason", required=True, help="the mandatory switch-off reason"
    )
    disable_parser = extension_commands.add_parser(
        "disable", help="switch a personal extension off in this clone"
    )
    disable_parser.add_argument("name", help="personal extension name")
    disable_parser.add_argument(
        "--reason", help="a note recorded in the clone's switches file"
    )
    enable_parser = extension_commands.add_parser(
        "enable", help="switch a disabled personal extension back on"
    )
    enable_parser.add_argument("name", help="personal extension name")


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Dispatch the parsed ``extension`` subcommand."""

    if args.extension_command == "trust":
        return _run_trust(args, stderr)
    if args.extension_command == "untrust":
        return _run_untrust(args, stderr)
    if args.extension_command == "list":
        return _run_list(args, stderr)
    if args.extension_command == "switch":
        # Imported where it is dispatched, not at module level:
        # switch_off borrows this module's _managed_directory and
        # _toml_string, so a top-level import either way is circular.
        from agentmarshal import switch_off

        return switch_off.run(args, stderr)
    if args.extension_command == "disable":
        return _run_disable(args, stderr)
    if args.extension_command == "enable":
        return _run_enable(args, stderr)
    print(f"extension: unknown command {args.extension_command}", file=stderr)
    return 1


def _resolve(stderr: TextIO) -> tuple[Placement, LocalState] | None:
    """Resolve the journal placement and its local state, or print why not.

    ``local_state`` always names the git common directory of the repository
    that holds the journal, so in a sidecar the grants file and the log
    land in the sidecar's own local state and the host never enters the
    call — and the working tree hashed is the journal repository's, the
    tree that commits the extension directories.
    """

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            "agentmarshal extension must be run inside an initialized project; "
            "run agentmarshal init in the repository first",
            file=stderr,
        )
        return None
    try:
        placement = resolve_placement(project_root)
        return placement, local_state(placement)
    except (PlacementError, LocalStateError) as error:
        # The message can carry a value the tool did not write — a host
        # path from project.json, git's own error text — so it is escaped
        # the way a transcript line is, as cli.py's placement does.
        print(escape_for_display(str(error)), file=stderr)
        return None


def _managed_directory(project_root: Path) -> Path:
    """The resolved ``.agentmarshal/extensions/`` of the working tree.

    The project root is resolved, then the two components below it are
    checked lexically: a symlink in an ancestor of the project is the
    operator's own path and no hazard, while a link at ``.agentmarshal``
    or ``extensions`` would land the extension outside the tree it is
    committed in.
    """

    root = project_root.resolve()
    managed = root / ".agentmarshal" / "extensions"
    for component in (managed.parent, managed):
        if component.is_symlink():
            raise ExtensionTrustError(f"refusing a symbolic link: {component}")
    return managed


def _extension_directory(managed: Path, name: str) -> Path:
    """The named extension's directory, or why it cannot be granted.

    Form is decided the manifest reader's way: a directory form and a file
    form for one name refuse together — which form the extension is would
    be ambiguous — a ``<name>.toml`` alone is a file-form extension with
    no directory to grant, and neither form is a missing extension. A
    symlinked ``<name>`` is refused as a link before existence is decided,
    dangling or not, the same refusal the manifest reader applies.
    """

    directory = managed / name
    file_form = managed / f"{name}.toml"
    if directory.is_symlink():
        raise ExtensionTrustError(f"refusing a symbolic link: {directory}")
    if directory.is_dir():
        if file_form.exists() or file_form.is_symlink():
            raise ExtensionTrustError(
                f"extension {name!r} has both the file and the directory "
                f"form: {file_form} and {directory}"
            )
        return directory
    if file_form.exists() or file_form.is_symlink():
        raise ExtensionTrustError(
            f"extension {name!r} is a file-form extension; a single file "
            f"has no directory to grant: {file_form}"
        )
    if directory.exists():
        raise ExtensionTrustError(f"extension {name!r} is not a directory: {directory}")
    raise ExtensionTrustError(
        f"extension {name!r} is missing: {directory} does not exist"
    )


def read_personal_manifest(directory: Path, name: str) -> ExtensionManifest:
    """Read and validate one personal extension's manifest from the clone.

    A personal extension is a directory ``<name>/`` under the clone's
    ``LocalState.extensions`` carrying ``manifest.toml`` — the directory
    form alone (ADR-0013 decision 9), read from that directory and never
    the base. The same refusal rules as the shared directory form apply:
    a link at the directory or the manifest is refused as a link, schema
    2 is required, and every path the manifest names under ``bin/`` or
    ``lock/`` must exist inside the directory as a regular file. On top
    of those, decision 10's bound is checked on the raw table before the
    shared parser sees the text: a personal manifest carries no
    ``footprint``, ``documents`` or ``artifacts`` — a personal extension
    has no footprint in the repository — and the parser is handed the
    text with the two mandatory arrays supplied empty, so every other
    rule (stages, isolation, wraps, records) applies unchanged.

    The returned manifest exposes its directory, as the shared
    directory-form read does.
    """

    if directory.is_symlink():
        raise ExtensionManifestError(f"refusing to read through a symlink: {directory}")
    manifest_lexical = directory / "manifest.toml"
    if manifest_lexical.is_symlink():
        raise ExtensionManifestError(
            f"refusing to read through a symlink: {manifest_lexical}"
        )
    try:
        root = directory.resolve(strict=True)
    except FileNotFoundError:
        raise ExtensionManifestError(
            f"extension manifest {name!r} is missing: {manifest_lexical}"
        ) from None
    except (NotADirectoryError, OSError, RuntimeError) as error:
        raise ExtensionManifestError(
            f"cannot resolve extension manifest {name!r}: {error}"
        ) from error
    source = root / "manifest.toml"
    try:
        resolved = source.resolve(strict=True)
    except FileNotFoundError:
        raise ExtensionManifestError(
            f"extension manifest {name!r} is missing: {source}"
        ) from None
    except (NotADirectoryError, OSError, RuntimeError) as error:
        raise ExtensionManifestError(
            f"cannot resolve extension manifest {name!r}: {error}"
        ) from error
    if resolved != source:
        raise ExtensionManifestError(f"refusing to read through a symlink: {source}")
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ExtensionManifestError(
            f"cannot read extension manifest {name!r}: {error}"
        ) from error
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ExtensionManifestError(
            f"invalid TOML extension manifest: {source}"
        ) from error
    for field in ("footprint", "documents", "artifacts"):
        if field in raw:
            raise ExtensionManifestError(
                f"extension manifest field {field!r} is not allowed in a "
                f"personal manifest: {source}"
            )
    manifest = parse_extension_manifest_text(
        "footprint = []\ndocuments = []\n" + text, name, source
    )
    if manifest.schema != 2:
        raise ExtensionManifestError(
            "the directory form requires a manifest of schema 2; "
            f"{name!r} declares schema {manifest.schema}: {source}"
        )
    for relpath in _manifest_directory_paths(manifest):
        _require_existing_directory_file(root, relpath)
    return replace(manifest, directory=root)


def _hash_directory(directory: Path) -> dict[str, str]:
    """The sha256 of every regular file under *directory*, by relative path.

    The walk is manual, entry by entry in sorted order so the first
    refusal is deterministic: a symbolic link — to a file, to a
    directory, dangling or not — is refused naming its relative path
    before its type is weighed, and a recursive glob would instead
    follow a linked directory out of the extension. A regular file is
    hashed under its ``/``-joined relative path; a directory recurses;
    anything else refuses the grant naming it.
    """

    files: dict[str, str] = {}

    def walk(root: Path) -> None:
        try:
            entries = sorted(root.iterdir())
        except OSError as error:
            raise ExtensionTrustError(
                f"cannot read {root}: {error.strerror or error}"
            ) from error
        for entry in entries:
            relpath = entry.relative_to(directory).as_posix()
            if entry.is_symlink():
                raise ExtensionTrustError(
                    f"a symbolic link inside the extension's directory: {relpath}"
                )
            if entry.is_dir():
                walk(entry)
                continue
            if entry.is_file():
                try:
                    files[relpath] = hashlib.sha256(entry.read_bytes()).hexdigest()
                except OSError as error:
                    raise ExtensionTrustError(
                        f"cannot read {entry}: {error.strerror or error}"
                    ) from error
                continue
            raise ExtensionTrustError(
                f"not a regular file inside the extension's directory: {relpath}"
            )

    walk(directory)
    return files


def _directory_hash(files: dict[str, str]) -> str:
    """One hash over the sorted path-and-hash list.

    Each file contributes its relative path's UTF-8 bytes, a NUL, its
    lowercase hex sha256 and another NUL — NUL cannot occur in a path,
    so the framing is unambiguous and the value depends on contents
    alone: same files, same hash, whatever order the filesystem hands
    back.
    """

    hasher = hashlib.sha256()
    for path in sorted(files):
        hasher.update(path.encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(files[path].encode("ascii"))
        hasher.update(b"\x00")
    return hasher.hexdigest()


def _read_grants(trust_file: Path) -> dict[str, Grant]:
    """Read ``trust.toml`` fail-closed; a missing file is no grants.

    Anything short of the recorded shape refuses naming the file: an
    unreadable file, text that is not TOML, a missing or unknown
    ``format``, and a grant that is not a table of the recorded fields.
    Extra keys pass unread — a newer local format may add them.
    """

    try:
        raw = trust_file.read_bytes()
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise ExtensionTrustError(
            f"{trust_file}: cannot read the trust file: {error.strerror or error}"
        ) from error
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise ExtensionTrustError(f"{trust_file}: malformed: {error}") from error
    version = data.get("format")
    if version is None:
        raise ExtensionTrustError(f"{trust_file}: missing 'format'")
    # `type` and equality both: bool is a subclass of int, so `True` and
    # `1.0` each compare equal to `1` — only an exact int 1 is the known
    # format.
    if not (type(version) is int and version == TRUST_FORMAT):
        raise ExtensionTrustError(f"{trust_file}: unknown format {version!r}")
    grants_table = data.get("grants", {})
    if not isinstance(grants_table, dict):
        raise ExtensionTrustError(f"{trust_file}: malformed: 'grants' is not a table")
    grants: dict[str, Grant] = {}
    for name, entry in grants_table.items():
        malformed = f"{trust_file}: malformed: grant {name!r}"
        if not isinstance(entry, dict):
            raise ExtensionTrustError(f"{malformed} is not a table")
        directory_hash = entry.get("directory_hash")
        granted_by = entry.get("granted_by")
        granted_by_source = entry.get("granted_by_source")
        granted_at = entry.get("granted_at")
        files = entry.get("files")
        if not (
            isinstance(directory_hash, str)
            and isinstance(granted_by, str)
            and isinstance(granted_by_source, str)
            and isinstance(granted_at, str)
            and isinstance(files, dict)
            and all(isinstance(v, str) for v in files.values())
        ):
            raise ExtensionTrustError(
                f"{malformed} lacks a field or carries a field of the wrong type"
            )
        grants[name] = Grant(
            directory_hash=directory_hash,
            granted_by=granted_by,
            granted_by_source=granted_by_source,
            granted_at=granted_at,
            files=dict(files),
        )
    return grants


def _toml_string(value: str) -> str:
    """*value* as a TOML basic string — quoted and escaped."""

    escaped = "".join(
        _TOML_ESCAPES[character]
        if character in _TOML_ESCAPES
        else f"\\u{ord(character):04X}"
        if ord(character) < 0x20 or ord(character) == 0x7F
        else character
        for character in value
    )
    return f'"{escaped}"'


def _dump_grants(grants: dict[str, Grant]) -> str:
    """Serialize the grants table — the one fixed shape the file holds."""

    lines = ["format = 1", ""]
    for name in sorted(grants):
        grant = grants[name]
        lines.append(f"[grants.{_toml_string(name)}]")
        lines.append(f"directory_hash = {_toml_string(grant.directory_hash)}")
        lines.append(f"granted_by = {_toml_string(grant.granted_by)}")
        lines.append(f"granted_by_source = {_toml_string(grant.granted_by_source)}")
        lines.append(f"granted_at = {_toml_string(grant.granted_at)}")
        lines.append("")
        lines.append(f"[grants.{_toml_string(name)}.files]")
        for path in sorted(grant.files):
            lines.append(f"{_toml_string(path)} = {_toml_string(grant.files[path])}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _write_grants(state: LocalState, grants: dict[str, Grant]) -> None:
    """Write ``trust.toml`` atomically: a temporary file renamed into place.

    The staging file sits in the local state root — created through the
    contained creation call — so the rename is same-directory and a reader
    never meets a half-written file; a failure anywhere leaves the
    previous file whole and the staging file unlinked.
    """

    root = state.ensure_directory(state.root)
    descriptor, staging_name = tempfile.mkstemp(
        dir=root, prefix=".trust-", suffix=".tmp"
    )
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(_dump_grants(grants))
        os.replace(staging, state.trust_file)
    except Exception:
        staging.unlink(missing_ok=True)
        raise


def _changed_after_approval(
    granted: dict[str, str], current: dict[str, str]
) -> tuple[str, str] | None:
    """The first differing file by sorted path and its kind, or ``None``.

    Compared per file, not per directory hash — the per-file record is
    the substance, and the file the run-time check will owe its refusal
    is exactly this one: removed, added or changed, in path order.
    """

    for path in sorted(set(granted) | set(current)):
        if path not in current:
            return path, "removed"
        if path not in granted:
            return path, "added"
        if granted[path] != current[path]:
            return path, "changed"
    return None


def _run_trust(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        _validate_name(args.name)
    except ExtensionManifestError as error:
        print(f"extension trust: {error}", file=stderr)
        return 1
    resolved = _resolve(stderr)
    if resolved is None:
        return 1
    placement, state = resolved
    # A malformed file refuses ahead of every other check, so it names
    # the file however the rest of the run would have failed.
    try:
        grants = _read_grants(state.trust_file)
    except ExtensionTrustError as error:
        print(f"extension trust: {escape_for_display(str(error))}", file=stderr)
        return 1
    try:
        managed = _managed_directory(placement.project_root)
        directory = _extension_directory(managed, args.name)
        files = _hash_directory(directory)
    except ExtensionTrustError as error:
        print(f"extension trust: {escape_for_display(str(error))}", file=stderr)
        return 1
    # The grant requires its granter, so the resolution is decided here,
    # before anything is written — on the same root every record
    # resolves it from.
    actor = resolve_recorded_by(placement.project_root)
    if actor is None:
        print(
            "extension trust: no granter identity could be resolved; set "
            "AGENTMARSHAL_ACTOR or configure git user.email",
            file=stderr,
        )
        return 1
    recorder, source = actor
    grant = Grant(
        directory_hash=_directory_hash(files),
        granted_by=recorder,
        granted_by_source=source,
        granted_at=datetime.now(UTC).isoformat(timespec="microseconds"),
        files=files,
    )
    grants[args.name] = grant
    try:
        _write_grants(state, grants)
    except (LocalStateError, OSError) as error:
        print(f"extension trust: {escape_for_display(str(error))}", file=stderr)
        return 1
    try:
        writer = open_writer(state)
        write_event(
            writer,
            "trust-changed",
            extension=args.name,
            action="granted",
            directory_hash=grant.directory_hash,
            actor=recorder,
        )
    except (LocalStateError, ProcessLogError, OSError) as error:
        reason = (
            error.strerror or str(error) if isinstance(error, OSError) else str(error)
        )
        print(
            f"extension trust: the grant was written but its event was not: "
            f"{escape_for_display(reason)}",
            file=stderr,
        )
        return 1
    print(state.trust_file)
    print(f"granted {escape_for_display(args.name)}")
    print(f"directory hash {grant.directory_hash}")
    print(f"granted by {escape_for_display(recorder)}")
    return 0


def _run_untrust(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        _validate_name(args.name)
    except ExtensionManifestError as error:
        print(f"extension untrust: {error}", file=stderr)
        return 1
    resolved = _resolve(stderr)
    if resolved is None:
        return 1
    placement, state = resolved
    try:
        grants = _read_grants(state.trust_file)
    except ExtensionTrustError as error:
        print(f"extension untrust: {escape_for_display(str(error))}", file=stderr)
        return 1
    grant = grants.pop(args.name, None)
    if grant is None:
        print(
            f"extension untrust: no grant recorded for {escape_for_display(args.name)}",
            file=stderr,
        )
        return 1
    try:
        _write_grants(state, grants)
    except (LocalStateError, OSError) as error:
        print(f"extension untrust: {escape_for_display(str(error))}", file=stderr)
        return 1
    actor = resolve_recorded_by(placement.project_root)
    try:
        writer = open_writer(state)
        if actor is None:
            write_event(
                writer,
                "trust-changed",
                extension=args.name,
                action="removed",
                directory_hash=grant.directory_hash,
            )
        else:
            write_event(
                writer,
                "trust-changed",
                extension=args.name,
                action="removed",
                actor=actor[0],
                directory_hash=grant.directory_hash,
            )
    except (LocalStateError, ProcessLogError, OSError) as error:
        reason = (
            error.strerror or str(error) if isinstance(error, OSError) else str(error)
        )
        print(
            f"extension untrust: the grant was removed but its event was not: "
            f"{escape_for_display(reason)}",
            file=stderr,
        )
        return 1
    print(state.trust_file)
    print(f"removed grant for {escape_for_display(args.name)}")
    return 0


def _run_list(args: argparse.Namespace, stderr: TextIO) -> int:
    resolved = _resolve(stderr)
    if resolved is None:
        return 1
    placement, state = resolved
    try:
        grants = _read_grants(state.trust_file)
        managed = _managed_directory(placement.project_root)
    except ExtensionTrustError as error:
        print(f"extension list: {escape_for_display(str(error))}", file=stderr)
        return 1
    try:
        entries = sorted(managed.iterdir()) if managed.is_dir() else []
    except OSError as error:
        print(
            f"extension list: cannot read {managed}: "
            f"{escape_for_display(error.strerror or str(error))}",
            file=stderr,
        )
        return 1
    for entry in entries:
        name = escape_for_display(entry.name)
        if entry.is_symlink():
            print(f"{name}: a symbolic link — not a real directory")
            continue
        if not entry.is_dir():
            continue
        try:
            files = _hash_directory(entry)
        except ExtensionTrustError as error:
            print(f"{name}: {escape_for_display(str(error))}")
            continue
        grant = grants.get(entry.name)
        if grant is None:
            print(f"{name}: not granted")
            continue
        difference = _changed_after_approval(grant.files, files)
        if difference is None:
            print(f"{name}: granted")
        else:
            path, kind = difference
            print(
                f"{name}: changed after approval: {escape_for_display(path)} ({kind})"
            )
    return 0


def _dump_personal_switches(switches: dict[str, PersonalSwitch]) -> str:
    """Serialize the personal switches table — the one shape the file holds.

    The ``[switches]`` header is always written, so a file whose last
    entry was removed still holds the table the parser requires.
    """

    lines = ["format = 1", "", "[switches]", ""]
    for name in sorted(switches):
        switch = switches[name]
        lines.append(f"[switches.{_toml_string(name)}]")
        lines.append(f"state = {_toml_string(switch.state)}")
        if switch.reason is not None:
            lines.append(f"reason = {_toml_string(switch.reason)}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _write_personal_switches(
    state: LocalState, switches: dict[str, PersonalSwitch]
) -> None:
    """Write the clone's ``switches.toml`` atomically, the grants file's way."""

    root = state.ensure_directory(state.root)
    descriptor, staging_name = tempfile.mkstemp(
        dir=root, prefix=".switches-", suffix=".tmp"
    )
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(_dump_personal_switches(switches))
        os.replace(staging, state.switches_file)
    except Exception:
        staging.unlink(missing_ok=True)
        raise


def _shared_name_refusal(command: str, name: str) -> str:
    """The one line every personal switch prints for a shared extension."""

    return (
        f"extension {command}: {escape_for_display(name)}: a shared "
        "extension is switched off only by an operational task "
        "(extension switch off)"
    )


def _personal_names(
    command: str, state: LocalState, stderr: TextIO
) -> frozenset[str] | None:
    """Enumerate the clone's personal extensions, or print why not."""

    try:
        return personal_extension_names(state.extensions)
    except OSError as error:
        print(
            f"extension {command}: cannot enumerate {state.extensions}: "
            f"{escape_for_display(error.strerror or str(error))}",
            file=stderr,
        )
        return None


def _run_disable(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        _validate_name(args.name)
    except ExtensionManifestError as error:
        print(f"extension disable: {error}", file=stderr)
        return 1
    reason: str | None = args.reason
    if reason is not None:
        if not reason or len(reason) > REASON_CHAR_LIMIT:
            print(
                f"extension disable: --reason must be a non-empty string of "
                f"at most {REASON_CHAR_LIMIT} characters",
                file=stderr,
            )
            return 1
        try:
            reject_control_characters(reason, "extension disable field 'reason'")
        except JournalContractError as error:
            print(
                f"extension disable: {escape_for_display(str(error))}",
                file=stderr,
            )
            return 1
    resolved = _resolve(stderr)
    if resolved is None:
        return 1
    placement, state = resolved
    try:
        managed = _managed_directory(placement.project_root)
    except ExtensionTrustError as error:
        print(f"extension disable: {escape_for_display(str(error))}", file=stderr)
        return 1
    if args.name in shared_extension_names(managed):
        print(_shared_name_refusal("disable", args.name), file=stderr)
        return 1
    names = _personal_names("disable", state, stderr)
    if names is None:
        return 1
    if args.name not in names:
        print(
            f"extension disable: {escape_for_display(args.name)} is not a "
            "personal extension",
            file=stderr,
        )
        return 1
    try:
        switches = read_personal_switches(state.switches_file, names)
    except SwitchesError as error:
        print(f"extension disable: {escape_for_display(str(error))}", file=stderr)
        return 1
    switches[args.name] = PersonalSwitch(state="off", reason=reason)
    try:
        _write_personal_switches(state, switches)
    except (LocalStateError, OSError) as error:
        print(f"extension disable: {escape_for_display(str(error))}", file=stderr)
        return 1
    print(state.switches_file)
    print(f"disabled {escape_for_display(args.name)}")
    return 0


def _run_enable(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        _validate_name(args.name)
    except ExtensionManifestError as error:
        print(f"extension enable: {error}", file=stderr)
        return 1
    resolved = _resolve(stderr)
    if resolved is None:
        return 1
    placement, state = resolved
    try:
        managed = _managed_directory(placement.project_root)
    except ExtensionTrustError as error:
        print(f"extension enable: {escape_for_display(str(error))}", file=stderr)
        return 1
    if args.name in shared_extension_names(managed):
        print(_shared_name_refusal("enable", args.name), file=stderr)
        return 1
    names = _personal_names("enable", state, stderr)
    if names is None:
        return 1
    try:
        # `names | {name}`: an entry may outlive its extension — the
        # switch of a deleted personal extension is still removable.
        switches = read_personal_switches(state.switches_file, names | {args.name})
    except SwitchesError as error:
        print(f"extension enable: {escape_for_display(str(error))}", file=stderr)
        return 1
    switch = switches.get(args.name)
    if switch is None or switch.state != "off":
        print(
            f"extension enable: {escape_for_display(args.name)} is not disabled",
            file=stderr,
        )
        return 1
    del switches[args.name]
    try:
        _write_personal_switches(state, switches)
    except (LocalStateError, OSError) as error:
        print(f"extension enable: {escape_for_display(str(error))}", file=stderr)
        return 1
    print(state.switches_file)
    print(f"enabled {escape_for_display(args.name)}")
    return 0
