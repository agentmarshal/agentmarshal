"""The ``extension switch`` group: switch a shared extension off.

ADR-0013 decisions 16 and 17: a shared extension is switched off only
by an operational CR — its diff touches only
``.agentmarshal/switches.toml`` and its own task's records, the reason
is mandatory, and it is opened with one command, ``agentmarshal
extension switch off <name> --reason <text>``. This is that command: it
opens the task through the journal's own ``open_task`` — a generated
contract whose scope is exactly the switches file — and writes the
``off`` entry for the task it opened.

The name must be a shared extension the working tree declares — the
manifest reader's call, so a linked or unreadable manifest is refused
with the reader's own message — and the reason must pass the parser's
own rule, each checked with the existing file before the task is
opened, so an early refusal writes nothing. The rewrite is
textual — there is no TOML writer to add — an ``on`` entry has the
switch's own key/value lines inside its table replaced, every other
key and line kept, or a new table is appended; the new text is
verified before the task exists — it must parse to the old text
everywhere but the one switch, under a placeholder task id — and
verified again under the opened task's real id before the file is
swapped in atomically. An ``on`` entry whose table the command cannot
bound on its own lines — a multi-line value inside it holding a line
that reads as a table header — is refused before any task is opened;
switching it off is then an edit of the file in an operational task,
by hand. A failure once the task is opened is reported on one line
naming it. In a sidecar the command refuses: an operational CR's
force is the gate lane that admits its diff, and a sidecar gate
decides no merge.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import tomllib
from pathlib import Path
from typing import Any, TextIO

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
    ExtensionManifestMissing,
    _validate_name,
    read_extension_manifest,
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

#: A key in a table header — bare, a basic string or a literal string.
_HEADER_KEY = r"(?:[A-Za-z0-9_-]+|\"(?:[^\"\\]|\\.)*\"|'[^']*')"

#: A line that is a full TOML table or array-of-tables header by the
#: grammar — the only line that ends a table's own text. A ``[``-led
#: line inside a multi-line value is a continuation, not a header:
#: ``["a", "b"],`` fails for its trailing comma, ``[1, 2]`` for the
#: comma inside, so they do not bound the table. One that still
#: matches — a last array element ``["x"]`` on its own line — does,
#: and bounds the table short; the self-containedness check in
#: ``_entry_span`` is what refuses that.
_TABLE_HEADER = re.compile(
    r"^[ \t]*\[\[?[ \t]*"
    + _HEADER_KEY
    + r"(?:[ \t]*\.[ \t]*"
    + _HEADER_KEY
    + r")*[ \t]*\]\]?[ \t]*(?:#.*)?$"
)

#: The task id the new text is verified under before the task exists —
#: a ``CR-<n>`` of the valid form the journal's allocator never assigns.
_PLACEHOLDER_TASK = "CR-0"


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Dispatch the parsed ``extension switch`` subcommand."""

    if args.switch_command == "off":
        return _run_off(args, stderr)
    print(
        f"extension switch: unknown command {escape_for_display(args.switch_command)}",
        file=stderr,
    )
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


def _shared_extension_names(project_root: Path, managed: Path) -> frozenset[str]:
    """The shared extension names the working tree declares, in both forms.

    The candidates are *managed*'s entries — a ``<name>.toml`` entry or
    a ``<name>/`` directory, a symbolic-link entry under the name it
    carries — and a candidate is declared only when the manifest
    reader accepts it: a linked manifest or extension directory, a
    name claimed in both forms and a manifest that cannot be read each
    fail the reader, so they are no shared extension the file may
    name. The reader is the one rule — ``read_extension_manifest``
    decides here exactly as it decides for the name being switched
    off. A *managed* that is not a directory is simply no extensions.
    """

    candidates: set[str] = set()
    if managed.is_dir():
        for entry in sorted(managed.iterdir()):
            if entry.is_symlink():
                candidates.add(entry.name.removesuffix(".toml"))
            elif entry.is_dir():
                candidates.add(entry.name)
            elif entry.name.endswith(".toml"):
                candidates.add(entry.name.removesuffix(".toml"))
    names: set[str] = set()
    for name in sorted(candidates):
        try:
            read_extension_manifest(project_root, name)
        except ExtensionManifestError:
            continue
        names.add(name)
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
    """The line span of the ``[switches.<name>]`` table, or ``None``.

    The table runs from its header line to the line before the next
    table header — a line that is a full TOML table or array-of-tables
    header by the grammar, nothing shorter — or the file's end, and
    everything between is its own: comments, blanks, and the key/value
    lines of every key it carries. ``None`` when zero lines or more
    than one open the table — an ``on`` entry the parse found can be
    carried in a form with no header at all, an inline table or dotted
    keys under ``[switches]``, and a second match can only be a
    header-shaped line inside a multi-line value — and ``None`` when
    the lines the span claims do not form a complete TOML document on
    their own: a table's own lines are always a sequence of pairs, so a
    span that ends inside a multi-line value — cut short by a
    header-shaped line that is really a continuation, like a last
    array element ``["x"]`` — leaves a value unclosed and is no bound
    the command can trust.
    """

    matches = [
        index for index, line in enumerate(lines) if header.match(line.rstrip("\r"))
    ]
    if len(matches) != 1:
        return None
    start = matches[0]
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if _TABLE_HEADER.match(lines[index].rstrip("\r"))
        ),
        len(lines),
    )
    try:
        tomllib.loads(
            "\n".join(line.removesuffix("\r") for line in lines[start + 1 : end])
        )
    except tomllib.TOMLDecodeError:
        return None
    return start, end


def _key_pair(lines: list[str], lo: int, hi: int, key: str) -> tuple[int, int] | None:
    """The line span of the pair assigning *key* inside ``[lo, hi)``.

    The pair's first line is the one that opens with the key itself —
    bare, or in either quoted spelling — followed by ``=``; its last
    line is the one the value completes on, found by parsing the
    line's prefix: the smallest ``lines[start:end]`` that parses as a
    TOML document is exactly the pair, since a value an earlier cut
    leaves open — an array, an inline table, a multi-line string —
    does not parse, and nothing continues a pair past its line. An
    ``on`` entry's ``state`` and ``task`` are strings, so each is one
    pair somewhere in the table's own lines; ``None`` means there is
    not exactly one line the key could assign on — zero, or more than
    one where a line inside a multi-line value only reads as the key —
    or that the one found will not bound, and either way the entry is
    one the command cannot rewrite on its own.
    """

    pattern = re.compile(r"^[ \t]*(?:" + _key_spellings(key) + r")[ \t]*=")
    matches = [
        index
        for index in range(lo, hi)
        if pattern.match(lines[index].removesuffix("\r"))
    ]
    if len(matches) != 1:
        return None
    start = matches[0]
    for end in range(start + 1, hi + 1):
        try:
            tomllib.loads(
                "\n".join(line.removesuffix("\r") for line in lines[start:end])
            )
        except tomllib.TOMLDecodeError:
            continue
        return start, end
    return None


def _entry_body(
    lines: list[str],
    lo: int,
    hi: int,
    task_id: str,
    reason: str,
    crlf: bool,
) -> list[str] | None:
    """The table's own lines with the switch's pairs rewritten — or ``None``.

    ``state``'s pair is replaced by ``state = "off"`` and ``task``'s by
    the opened task's id with ``reason`` added after it — every other
    line of the table, keys the entry carries beyond the switch's own
    included, stays as it was. ``None`` when either pair cannot be
    located — the entry is then one the command cannot rewrite on its
    own lines.
    """

    suffix = "\r" if crlf else ""
    spans: dict[int, tuple[int, list[str]]] = {}
    for key, replacement in (
        ("state", ['state = "off"']),
        (
            "task",
            [f"task = {_toml_string(task_id)}", f"reason = {_toml_string(reason)}"],
        ),
    ):
        pair = _key_pair(lines, lo, hi, key)
        if pair is None:
            return None
        if any(start < pair[1] and pair[0] < end for start, (end, _) in spans.items()):
            # One located pair inside another's lines — a key-shaped
            # line inside a multi-line value. There is no safe rewrite.
            return None
        spans[pair[0]] = (pair[1], replacement)
    out: list[str] = []
    index = lo
    while index < hi:
        found = spans.get(index)
        if found is not None:
            end, replacement = found
            out.extend(line + suffix for line in replacement)
            index = end
        else:
            out.append(lines[index])
            index += 1
    return out


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
) -> str | None:
    """The file's new text, or ``None`` when the rewrite cannot be built.

    *text* is ``None`` when the file does not exist — it is created
    with ``format = 1`` and a ``[switches]`` table. *span* is the
    ``on`` entry's table: its ``state`` and ``task`` key/value lines
    are replaced by the off entry's — the header line, every other key
    the entry carries and every other line stay as they were — and
    when the table's pairs cannot be located on their own lines the
    result is ``None``: the entry is refused, not corrupted. When
    *span* is ``None`` the new table is appended after the file's
    existing content, on the file's own line-ending convention.
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
        body = _entry_body(lines, start + 1, end, task_id, reason, crlf)
        if body is None:
            return None
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


def _verify_rewrite(
    new_text: str,
    text: str | None,
    name: str,
    task_id: str,
    reason: str,
    switches_file: Path,
    names: frozenset[str],
) -> str | None:
    """Why *new_text* is not *text* with only the switch changed — or ``None``.

    The new text is trusted only as far as TOML itself proves it: the
    parsed new text must equal the parsed old text everywhere, with
    the one ``switches`` entry carrying the keys it carried plus the
    off entry's ``state``, ``task`` and ``reason`` — so a key the
    rewrite dropped shows here — and the shared parser must accept
    the file and read that entry back as ``off`` with *task_id* and
    *reason*. A missing file's old text is the empty document, checked
    against the skeleton the command creates. A mis-detected span, an
    ``on`` entry with no header to find, a rewritten value that is not
    what the lines claimed — anything that makes the new text differ
    where the switch does not reach — is named here.
    """

    try:
        new_data = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError as error:
        return f"the rewritten text is not TOML: {error}"
    expected: dict[str, Any] = (
        tomllib.loads(text) if text is not None else {"format": 1}
    )
    expected_entry = dict(expected.get("switches", {}).get(name) or {})
    expected_entry.update({"state": "off", "task": task_id, "reason": reason})
    expected.setdefault("switches", {})[name] = expected_entry
    if new_data != expected:
        return "the rewritten text changed more than the switch"
    try:
        written = parse_switches(new_text.encode("utf-8"), switches_file, names).get(
            name
        )
    except SwitchesError as error:
        return str(error)
    if (
        written is None
        or written.state != "off"
        or written.task != task_id
        or written.reason != reason
    ):
        return f"the off entry for {name!r} is missing"
    return None


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
        print(f"{_COMMAND}: {escape_for_display(str(error))}", file=stderr)
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
    # here — the name, the reason, the existing file and the rewrite
    # that is to land in it — so an early refusal leaves nothing
    # behind: no task, no file.
    try:
        names = _shared_extension_names(project_root, _managed_directory(project_root))
    except (ExtensionTrustError, OSError) as error:
        print(f"{_COMMAND}: {escape_for_display(str(error))}", file=stderr)
        return 1
    # Whether the name is a shared extension the working tree declares
    # is the manifest reader's call — not a second copy of its rules: a
    # missing manifest is "not declared", and any other refusal — a
    # linked manifest or extension directory, a manifest in both forms,
    # one that cannot be read — is reported with the reader's own
    # message, before anything is written.
    try:
        read_extension_manifest(project_root, args.name)
    except ExtensionManifestMissing:
        print(
            f"{_COMMAND}: '{escape_for_display(args.name)}' is not a shared "
            "extension the working tree declares",
            file=stderr,
        )
        return 1
    except ExtensionManifestError as error:
        print(
            f"{_COMMAND}: '{escape_for_display(args.name)}': "
            f"{escape_for_display(str(error))}",
            file=stderr,
        )
        return 1
    reason_error = _reason_error(args.reason)
    if reason_error is not None:
        print(f"{_COMMAND}: {escape_for_display(reason_error)}", file=stderr)
        return 1
    switches_file = project_root / SWITCHES_RELPATH
    if switches_file.is_symlink():
        print(
            f"{_COMMAND}: refusing a symbolic link: "
            f"{escape_for_display(str(switches_file))}",
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
    # The rewrite is produced and verified before the task exists, under
    # a placeholder task id of the valid form: a file whose text the
    # command cannot carry the switch through — an `on` entry whose
    # table it cannot bound on its own lines, a mis-detected span — is
    # refused here, so nothing is written and no task is opened;
    # switching it off is then an edit of the file in an operational
    # task, by hand.
    new_text: str | None = None
    if current is None or span is not None:
        new_text = _switches_text(text, args.name, span, _PLACEHOLDER_TASK, args.reason)
    if new_text is None:
        refusal: str | None = "its table could not be bounded on its own lines"
    else:
        checked = _verify_rewrite(
            new_text,
            text,
            args.name,
            _PLACEHOLDER_TASK,
            args.reason,
            switches_file,
            names,
        )
        refusal = (
            None if checked is None else f"the rewrite could not be verified: {checked}"
        )
    if refusal is not None:
        print(
            f"{_COMMAND}: {escape_for_display(str(switches_file))}: the "
            f"entry for '{escape_for_display(args.name)}' must be "
            "switched off by editing the file in an operational task — "
            f"{escape_for_display(refusal)}",
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
            f"contract id {escape_for_display(opened.replaced_id)!r} "
            "replaced with the assigned task id "
            f"{escape_for_display(opened.task_id)!r}",
            file=stderr,
        )
    # The same text again, with only the `task` value's string changed
    # to the opened task's id — and the same verification run over it
    # before the file is replaced.
    new_text = _switches_text(text, args.name, span, opened.task_id, args.reason)
    refusal = (
        "its table could not be bounded on its own lines"
        if new_text is None
        else _verify_rewrite(
            new_text,
            text,
            args.name,
            opened.task_id,
            args.reason,
            switches_file,
            names,
        )
    )
    if refusal is not None:
        print(
            f"{_COMMAND}: opened {escape_for_display(opened.task_id)} but "
            f"the rewritten {escape_for_display(str(switches_file))} "
            "failed its own checks — nothing was written: "
            f"{escape_for_display(refusal)}",
            file=stderr,
        )
        return 1
    assert new_text is not None
    try:
        _write_switches(project_root, switches_file, new_text)
    except OSError as error:
        print(
            f"{_COMMAND}: opened {escape_for_display(opened.task_id)} but "
            f"could not write {escape_for_display(str(switches_file))}: "
            f"{escape_for_display(error.strerror or str(error))}",
            file=stderr,
        )
        return 1
    print(escape_for_display(str(opened.contract_path)))
    print(escape_for_display(str(opened.record_path)))
    print(escape_for_display(str(switches_file)))
    return 0
