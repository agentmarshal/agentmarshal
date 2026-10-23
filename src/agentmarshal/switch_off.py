"""The ``extension switch`` group: switch a shared extension off.

ADR-0013 decisions 16 and 17: a shared extension is switched off only
by an operational CR — its diff touches only
``.agentmarshal/switches.toml`` and its own task's records, the reason
is mandatory, and it is opened with one command, ``agentmarshal
extension switch off <name> --reason <text>``. This is that command: it
opens the task through the journal's own ``open_task`` — a generated
contract whose scope is exactly the switches file — and writes the
``off`` entry for the task it opened.

The name must be a shared extension the working tree declares — a
``<name>.toml`` entry or a ``<name>/`` directory — and the reason must
pass the parser's own rule, each checked with the existing file before
the task is opened, so an early refusal writes nothing. The rewrite is
textual — there is no TOML writer to add — an ``on`` entry's table
replaced or a new one appended, the whole new text parsed back by
``parse_switches`` and swapped in atomically; a failure once the task
is opened is reported on one line naming it. In a sidecar the command
refuses: an operational CR's force is the gate lane that admits its
diff, and a sidecar gate decides no merge.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import TextIO

from agentmarshal.extension_trust import (
    ExtensionTrustError,
    _managed_directory,
    _toml_string,
)
from agentmarshal.journal.contracts import (
    JournalContractError,
    reject_control_characters,
)
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    ExtensionManifestError,
    _validate_name,
)
from agentmarshal.journal.open_task import (
    OpenedTask,
    TaskOpenError,
    open_task,
)
from agentmarshal.journal.placement import (
    Placement,
    PlacementError,
    resolve_placement,
)
from agentmarshal.project import find_project_root
from agentmarshal.switches import (
    REASON_CHAR_LIMIT,
    SWITCHES_RELPATH,
    Switch,
    SwitchesError,
    parse_switches,
)

_COMMAND = "extension switch off"

#: A TOML bare key — anything else is written as a quoted string.
_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+$")

#: A line that opens any table — where one table's text ends.
_ANY_TABLE_HEADER = re.compile(r"[ \t]*\[")


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Dispatch the parsed ``extension switch`` subcommand."""

    if args.switch_command == "off":
        return _run_off(args, stderr)
    print(f"extension switch: unknown command {args.switch_command}", file=stderr)
    return 1


def _placement(stderr: TextIO) -> Placement | None:
    """Resolve the journal placement, or print why not — cli.py's pattern.

    ``require_host`` is not passed: the command never touches the host —
    in a sidecar it refuses outright, and everywhere else the working
    tree it reads and writes is the project root's own.
    """

    project_root = find_project_root(Path.cwd())
    if project_root is None:
        print(
            f"agentmarshal {_COMMAND} must be run inside an initialized "
            "project; run agentmarshal init in the repository first",
            file=stderr,
        )
        return None
    try:
        return resolve_placement(project_root)
    except PlacementError as error:
        # The message can carry a value the tool did not write — a host
        # path from project.json — so it is escaped the way cli.py's
        # placement escapes it.
        print(escape_for_display(str(error)), file=stderr)
        return None


def _shared_extension_names(managed: Path) -> frozenset[str]:
    """The extension names under *managed*, in both forms.

    The working-tree enumeration the manifest readers share — a
    ``<name>.toml`` entry is the file form and a ``<name>/`` entry the
    directory form, and a symbolic-link entry is kept under the name it
    carries — so a name this check admits is one the switches parser
    admits too, in either form. A ``managed`` that is not a directory
    is simply no extensions.
    """

    names: set[str] = set()
    if not managed.is_dir():
        return frozenset(names)
    for entry in sorted(managed.iterdir()):
        if entry.is_symlink():
            names.add(entry.name.removesuffix(".toml"))
        elif entry.is_dir():
            names.add(entry.name)
        elif entry.name.endswith(".toml"):
            names.add(entry.name.removesuffix(".toml"))
    return frozenset(names)


def _reason_error(reason: str) -> str | None:
    """The parser's own reason rule, applied before the reason is written.

    ``parse_switches`` refuses an ``off`` entry whose reason is empty,
    over ``REASON_CHAR_LIMIT`` characters or carrying a character the
    forgeable-text rule refuses — ``--reason`` is held to the same rule
    before anything is written, so the file the command writes can
    never carry a reason the parser refuses.
    """

    if not reason:
        return "--reason must not be empty: an 'off' switch needs a reason"
    if len(reason) > REASON_CHAR_LIMIT:
        return f"--reason is over {REASON_CHAR_LIMIT} characters"
    try:
        reject_control_characters(reason, "--reason")
    except JournalContractError as error:
        return str(error)
    return None


def _table_key(name: str) -> str:
    """*name* as a TOML key — bare where it may be, a quoted string else."""

    if _BARE_KEY.fullmatch(name):
        return name
    return _toml_string(name)


def _key_spellings(name: str) -> str:
    """A regex alternative matching every key spelling of *name*.

    A TOML key is bare, a basic string or a literal string; the
    spellings are the forms the file could carry for the one parsed
    name the header is located by.
    """

    spellings = [re.escape(_toml_string(name))]
    if _BARE_KEY.fullmatch(name):
        spellings.append(re.escape(name))
    if "'" not in name:
        spellings.append(re.escape(f"'{name}'"))
    return "(?:" + "|".join(spellings) + ")"


def _entry_header(name: str) -> re.Pattern[str]:
    """The pattern for the ``[switches.<name>]`` table's header line."""

    return re.compile(
        r"^[ \t]*\[[ \t]*"
        + _key_spellings("switches")
        + r"[ \t]*\.[ \t]*"
        + _key_spellings(name)
        + r"[ \t]*\][ \t]*(?:#.*)?$"
    )


def _entry_span(lines: list[str], header: re.Pattern[str]) -> tuple[int, int] | None:
    """The line span of the ``[switches.<name>]`` table's own text.

    The table runs from its header line to the line before the next
    table header or the file's end; the span returned ends at the
    table's last content line, so the blank and comment lines that
    trail it — the file's own spacing and notes — stay as they were.
    ``None`` when zero lines or more than one open the table: an ``on``
    entry the parse found can be carried in a form with no header — an
    inline table or dotted keys under ``[switches]`` — and a duplicate
    match can only be a line that is not a header at all, like one
    inside a multi-line string. Either way there is no one table to
    replace.
    """

    matches = [
        index for index, line in enumerate(lines) if header.match(line.rstrip("\r"))
    ]
    if len(matches) != 1:
        return None
    start = matches[0]
    last = start
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if _ANY_TABLE_HEADER.match(line):
            break
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            last = index
    return start, last + 1


def _entry_lines(task_id: str, reason: str) -> list[str]:
    """The off entry's key/value lines, in the file's own field order."""

    return [
        'state = "off"',
        f"task = {_toml_string(task_id)}",
        f"reason = {_toml_string(reason)}",
    ]


def _switches_text(
    text: str | None,
    name: str,
    span: tuple[int, int] | None,
    task_id: str,
    reason: str,
) -> str:
    """The file's new text: the off entry in, everything else as it was.

    *text* is ``None`` when the file does not exist — it is created
    with ``format = 1`` and a ``[switches]`` table. *span* is the
    ``on`` entry's table to replace — the header line stays as it was
    found — and when it is ``None`` the new table is appended after the
    file's existing content, on the file's own line-ending convention.
    """

    if text is None:
        return (
            "format = 1\n\n[switches]\n\n"
            f"[switches.{_table_key(name)}]\n"
            + "\n".join(_entry_lines(task_id, reason))
            + "\n"
        )
    crlf = "\r\n" in text
    if span is not None:
        lines = text.split("\n")
        start, end = span
        body = [line + ("\r" if crlf else "") for line in _entry_lines(task_id, reason)]
        return "\n".join(lines[: start + 1] + body + lines[end:])
    eol = "\r\n" if crlf else "\n"
    addition = (
        eol.join([f"[switches.{_table_key(name)}]", *_entry_lines(task_id, reason)])
        + eol
    )
    if not text.endswith("\n"):
        text += "\n"
    if not text.endswith("\n\n"):
        text += "\n"
    return text + addition


def _contract_text(name: str, reason: str) -> str:
    """The operational task's contract: the one file, the one switch.

    The header's ``id`` is a placeholder ``open_task`` retargets to the
    assigned task id — the value is never ``CR-000``, the one id the
    journal's allocator cannot produce, so the rewrite is always a
    replacement and is announced the way ``open`` announces it.
    """

    title = f"switch off the shared extension {name}"
    acceptance = (
        f"the shared extension {name} is switched off in "
        f"{SWITCHES_RELPATH} with the reason {reason}"
    )
    return (
        "+++\n"
        "schema = 2\n"
        'id = "CR-000"\n'
        f"title = {json.dumps(title, ensure_ascii=False)}\n"
        f"scope = [{json.dumps(SWITCHES_RELPATH)}]\n"
        f"acceptance = [{json.dumps(acceptance, ensure_ascii=False)}]\n"
        'decisions = ["ADR-0013"]\n'
        "+++\n\n"
        f"# {title}\n\n"
        "## Context\n\n"
        "ADR-0013 decision 16: a shared extension is switched off only by\n"
        "an operational CR. Decision 17: the operational CR touches only\n"
        "`.agentmarshal/switches.toml` (name → on/off, reason) and its own\n"
        "task's records; the reason is mandatory.\n\n"
        "## Objective\n\n"
        f"`{SWITCHES_RELPATH}` switches the shared extension {name} off —\n"
        '`state = "off"`, this task\'s id as `task` and the reason below\n'
        "as `reason`.\n\n"
        f"Reason: {reason}\n\n"
        "## Acceptance Criteria\n\n"
        f"- {acceptance}\n\n"
        "## Non-Goals\n\n"
        "- switching the extension back on — an `on` entry is an edit in\n"
        "  an operational task of its own.\n"
        "- changing the extension's directory, its grants or any other\n"
        "  file.\n"
    )


def _open_operational_task(project_root: Path, name: str, reason: str) -> OpenedTask:
    """Open the operational task from the generated contract.

    The contract is written to a temporary file and passed as
    ``contract_file`` — the journal's own opening transaction validates
    it, retargets its placeholder ``id`` to the assigned task id and
    pins its hash on the ``opened`` record. The temporary file is
    unlinked once the open returns.
    """

    descriptor, contract_name = tempfile.mkstemp(
        prefix=".switch-off-contract-", suffix=".md"
    )
    contract_file = Path(contract_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_contract_text(name, reason))
        return open_task(project_root, None, [], contract_file=contract_file)
    finally:
        contract_file.unlink(missing_ok=True)


def _write_switches(project_root: Path, switches_file: Path, text: str) -> None:
    """Write *text* over *switches_file* atomically.

    The staging file sits in the file's own directory — the
    same-directory rule ``_write_grants`` follows — so the rename can
    never cross filesystems and a reader never meets a half-written
    file; a failure anywhere leaves the previous file whole and the
    staging file unlinked.
    """

    descriptor, staging_name = tempfile.mkstemp(
        dir=project_root / ".agentmarshal", prefix=".switches-", suffix=".tmp"
    )
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(staging, switches_file)
    except Exception:
        staging.unlink(missing_ok=True)
        raise


def _read_existing(
    switches_file: Path, names: frozenset[str]
) -> tuple[str | None, dict[str, Switch]]:
    """The existing file's text and its parsed switches; a missing file is none.

    The read is the one ``read_switches`` performs, keeping the bytes
    the rewrite needs: a missing file is ``(None, {})`` — every
    extension on — and anything short of the recorded shape raises
    ``SwitchesError`` naming the file.
    """

    try:
        data = switches_file.read_bytes()
    except FileNotFoundError:
        return None, {}
    except OSError as error:
        raise SwitchesError(
            f"{switches_file}: cannot read the switches file: {error.strerror or error}"
        ) from error
    # The parse decoded these same bytes, so the decode cannot fail.
    return data.decode("utf-8"), parse_switches(data, switches_file, names)


def _run_off(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        _validate_name(args.name)
    except ExtensionManifestError as error:
        print(f"{_COMMAND}: {error}", file=stderr)
        return 1
    placement = _placement(stderr)
    if placement is None:
        return 1
    if placement.is_sidecar:
        print(
            f"{_COMMAND}: operational tasks are not available in a sidecar",
            file=stderr,
        )
        return 1
    project_root = placement.project_root
    # Everything that can be refused before the task exists is refused
    # here — the name, the reason and the existing file — so an early
    # refusal leaves nothing behind: no task, no file.
    try:
        names = _shared_extension_names(_managed_directory(project_root))
    except (ExtensionTrustError, OSError) as error:
        print(f"{_COMMAND}: {escape_for_display(str(error))}", file=stderr)
        return 1
    if args.name not in names:
        print(
            f"{_COMMAND}: '{escape_for_display(args.name)}' is not a shared "
            "extension the working tree declares",
            file=stderr,
        )
        return 1
    reason_error = _reason_error(args.reason)
    if reason_error is not None:
        print(f"{_COMMAND}: {reason_error}", file=stderr)
        return 1
    switches_file = project_root / SWITCHES_RELPATH
    if switches_file.is_symlink():
        print(
            f"{_COMMAND}: refusing a symbolic link: {switches_file}",
            file=stderr,
        )
        return 1
    try:
        text, switches = _read_existing(switches_file, names)
    except SwitchesError as error:
        print(f"{_COMMAND}: {escape_for_display(str(error))}", file=stderr)
        return 1
    current = switches.get(args.name)
    if current is not None and current.state == "off":
        print(
            f"{_COMMAND}: '{escape_for_display(args.name)}' is already "
            f"switched off by {escape_for_display(current.task)}",
            file=stderr,
        )
        return 1
    span: tuple[int, int] | None = None
    if current is not None:
        assert text is not None
        span = _entry_span(text.split("\n"), _entry_header(args.name))
        if span is None:
            print(
                f"{_COMMAND}: {switches_file}: the 'on' entry for "
                f"'{escape_for_display(args.name)}' is not a "
                "[switches.<name>] table this command can rewrite",
                file=stderr,
            )
            return 1
    try:
        opened = _open_operational_task(project_root, args.name, args.reason)
    except TaskOpenError as error:
        print(f"{_COMMAND}: {escape_for_display(str(error))}", file=stderr)
        return 1
    if opened.replaced_id is not None:
        print(
            f"contract id {opened.replaced_id!r} replaced with the "
            f"assigned task id {opened.task_id!r}",
            file=stderr,
        )
    new_text = _switches_text(text, args.name, span, opened.task_id, args.reason)
    refusal: str | None = None
    try:
        written = parse_switches(new_text.encode("utf-8"), switches_file, names).get(
            args.name
        )
    except SwitchesError as error:
        refusal = str(error)
    else:
        if (
            written is None
            or written.state != "off"
            or written.task != opened.task_id
            or written.reason != args.reason
        ):
            refusal = f"the off entry for {args.name!r} is missing"
    if refusal is not None:
        print(
            f"{_COMMAND}: opened {opened.task_id} but the rewritten "
            f"{switches_file} failed its own parse — nothing was "
            f"written: {escape_for_display(refusal)}",
            file=stderr,
        )
        return 1
    try:
        _write_switches(project_root, switches_file, new_text)
    except OSError as error:
        print(
            f"{_COMMAND}: opened {opened.task_id} but could not write "
            f"{switches_file}: "
            f"{escape_for_display(error.strerror or str(error))}",
            file=stderr,
        )
        return 1
    print(opened.contract_path)
    print(opened.record_path)
    print(switches_file)
    return 0
