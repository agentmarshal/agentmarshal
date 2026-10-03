"""Task opening transaction."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal import __version__
from agentmarshal.journal.contracts import (
    JournalContractError,
    contract_sha256,
    parse_contract_text,
)
from agentmarshal.journal.records import (
    JournalRecordError,
    create_opened_record,
    validate_task_id,
    write_record,
)

JOURNAL_ROOT_PARTS = (".agentmarshal", "journal")
_TASK_ID_PATTERN = re.compile(r"CR-(\d+)$")
_LEGACY_TASK_ID_PATTERN = re.compile(r"CR-(\d+)-.+\.md$")


class TaskOpenError(Exception):
    """Raised when a task cannot be opened."""


@dataclass(frozen=True)
class OpenedTask:
    """Paths created by a successful task opening transaction."""

    task_id: str
    contract_path: Path
    record_path: Path
    scope: tuple[str, ...] = ()
    replaced_id: str | None = None


def journal_root(project_root: Path) -> Path:
    """Return the journal root for an initialized project."""

    return project_root.joinpath(*JOURNAL_ROOT_PARTS)


def next_task_id(root: Path) -> str:
    """Allocate the next CR task number from existing task directories."""

    tasks_directory = root / "tasks"
    if tasks_directory.is_symlink():
        raise TaskOpenError(f"refusing to write through a symlink: {tasks_directory}")
    if not tasks_directory.exists():
        return "CR-001"
    if not tasks_directory.is_dir():
        raise TaskOpenError(f"task path is not a directory: {tasks_directory}")
    highest = 0
    for path in tasks_directory.rglob("*"):
        match = _TASK_ID_PATTERN.fullmatch(path.name)
        if match is None and path.is_file():
            match = _LEGACY_TASK_ID_PATTERN.fullmatch(path.name)
        if match is not None:
            highest = max(highest, int(match.group(1)))
    return f"CR-{highest + 1:03d}"


_CONTRACT_ID_KEY = re.compile(r"^[ \t]*(?:id|\"id\"|'id')[ \t]*=[ \t]*")

# Every boundary ``splitlines`` honours, longest first so ``\r\n`` is not
# mistaken for ``\r``: ``parse_contract_text`` splits on each of them and
# rejoins with ``\n``, so any is a line ending a contract may carry.
_LINE_ENDINGS = (
    "\r\n",
    "\n",
    "\r",
    "\v",
    "\f",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x85",
    "\u2028",
    "\u2029",
)

_AFTER_VALUE = re.compile(r"[ \t]*(?:#.*)?")

_ID_FORMS_MESSAGE = (
    "the header's `id` is not written in a form `open` can rewrite: it "
    "must be the key `id`, `\"id\"` or `'id'` with a one-line string "
    "value on a line of its own in the header's top-level table"
)


def _split_for_rewrite(text: str) -> tuple[str, list[str]]:
    """The text's leading byte-order marks and its lines, endings kept.

    ``parse_contract_text`` strips every leading mark and splits on every
    boundary ``splitlines`` knows — a lone CR included — so the rewrite
    works on the same lines and never reconstructs an ending; the bytes
    that were there stay.
    """

    stripped = text.lstrip("\ufeff")
    bom = text[: len(text) - len(stripped)]
    return bom, stripped.splitlines(keepends=True)


def _line_content(line: str) -> str:
    """A ``splitlines`` line without the boundary it was split on."""

    for ending in _LINE_ENDINGS:
        if line.endswith(ending):
            return line[: -len(ending)]
    return line


def _string_value_end(text: str) -> int | None:
    """The end of the one-line TOML string value opening *text*.

    *text* is what follows the ``=`` of an ``id`` line, its line ending
    excluded. A pattern cannot decide where the value ends — a multi-line
    string may carry up to two quote characters just before its closing
    delimiter, so ``id = \"\"\"CR-099\"\"\"\"`` is one string ending at
    the last quote — so TOML itself decides: the end is the shortest
    prefix that parses as a string, after which only whitespace and an
    optional comment remain on the line.
    """

    if not text.startswith(('"', "'")):
        return None
    for end in range(1, len(text) + 1):
        try:
            value = tomllib.loads("k = " + text[:end])["k"]
        except tomllib.TOMLDecodeError:
            continue
        if not isinstance(value, str):
            continue
        if _AFTER_VALUE.fullmatch(text[end:]) is not None:
            return end
    return None


def _id_line_candidates(lines: list[str]) -> list[tuple[int, int, int]]:
    """Header lines writing ``id`` in a form the open can rewrite.

    Each entry is the line's index and the offsets within it of the id's
    value: a line whose key is ``id``, ``"id"`` or ``'id'`` followed by
    ``=``, and whose value is a one-line string.
    """

    start = next(index for index, line in enumerate(lines) if line.strip() == "+++")
    end = next(
        index
        for index, line in enumerate(lines[start + 1 :], start + 1)
        if line.strip() == "+++"
    )
    candidates = []
    for index in range(start + 1, end):
        match = _CONTRACT_ID_KEY.match(lines[index])
        if match is None:
            continue
        value_end = _string_value_end(_line_content(lines[index])[match.end() :])
        if value_end is not None:
            candidates.append((index, match.end(), match.end() + value_end))
    return candidates


def _id_source_line(
    lines: list[str], header_id: str, bom: str
) -> tuple[int, int, int] | None:
    """Which candidate line actually declares the parsed ``id``.

    A line in a supported form is the declaration only where rewriting it
    changes what the header parses as ``id``: the same text inside a
    multi-line string value, or under a ``[table]`` header, matches the
    key pattern without being it. The probe only has to be a value the
    parsed id is not — rewriting the source line makes ``id`` parse as
    the probe, while rewriting a line that merely matches the pattern
    leaves ``id`` as it was — so it is a fixed ASCII value, NUL unless
    the parsed id is NUL itself, whose ``json.dumps`` encoding TOML
    always accepts whatever the author's id carries: a non-BMP character
    would be written as surrogate escapes TOML refuses.
    """

    probe_id = "\x00" if header_id != "\x00" else "\x00\x00"
    for index, value_start, value_end in _id_line_candidates(lines):
        line = lines[index]
        rewritten = (
            bom
            + "".join(lines[:index])
            + line[:value_start]
            + json.dumps(probe_id)
            + line[value_end:]
            + "".join(lines[index + 1 :])
        )
        try:
            parsed = parse_contract_text(rewritten, "the rewritten contract")
        except JournalContractError:
            continue
        if parsed.id == probe_id:
            return index, value_start, value_end
    return None


def _read_provided_contract(contract_file: Path) -> tuple[str, str, tuple[str, ...]]:
    """Read and validate a contract supplied on the command line.

    Returns the contract's text, the id its header declares and its declared
    scope. The header is validated exactly as ``parse_contract_text``
    validates a contract already in the journal — the boundary a malformed
    declaration is refused at, before anything it names is trusted — and
    its ``id`` must sit where the open can rewrite it, so a contract whose
    ``id`` is written another way is refused here too, before the journal
    is touched.
    """

    try:
        content = contract_file.read_bytes()
    except OSError as error:
        raise TaskOpenError(
            f"could not read contract file {contract_file}: {error}"
        ) from error
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise TaskOpenError(
            f"contract file is not valid UTF-8: {contract_file}"
        ) from error
    try:
        header = parse_contract_text(text, str(contract_file))
    except JournalContractError as error:
        raise TaskOpenError(str(error)) from error
    bom, lines = _split_for_rewrite(text)
    if _id_source_line(lines, header.id, bom) is None:
        raise TaskOpenError(f"contract file {contract_file}: {_ID_FORMS_MESSAGE}")
    return text, header.id, header.scope


def _retarget_contract_id(text: str, task_id: str) -> str:
    """Return *text* with the header's ``id`` set to *task_id*.

    Every other byte is kept: the contract was written first, and the text
    its hash is pinned over should differ from the author's only in the id
    the open assigns. Only the id's value is replaced — the rest of the
    line is the author's: key quoting, trailing whitespace, a comment, and
    the line ending, whatever it is.
    """

    bom, lines = _split_for_rewrite(text)
    located = _id_source_line(
        lines, parse_contract_text(text, "the provided contract").id, bom
    )
    if located is None:
        raise TaskOpenError(_ID_FORMS_MESSAGE)
    index, value_start, value_end = located
    line = lines[index]
    lines[index] = line[:value_start] + json.dumps(task_id) + line[value_end:]
    rewritten = bom + "".join(lines)
    # The header parsed before the rewrite and the line the probe named
    # was rewritten, so this confirms rather than checks: the retargeted
    # contract still parses and now names the task.
    if parse_contract_text(rewritten, "the rewritten contract").id != task_id:
        raise TaskOpenError("could not set the contract id to the assigned task id")
    return rewritten


def _contract_content(task_id: str, title: str, scope: list[str]) -> str:
    encoded_scope = ", ".join(json.dumps(item, ensure_ascii=False) for item in scope)
    encoded_title = json.dumps(title, ensure_ascii=False)
    return (
        "+++\n"
        "schema = 1\n"
        f"id = {json.dumps(task_id)}\n"
        f"title = {encoded_title}\n"
        f"scope = [{encoded_scope}]\n"
        "acceptance = []\n"
        "+++\n\n"
        f"# {task_id}: {title}\n\n"
        "## Context\n\n"
        "TODO\n\n"
        "## Objective\n\n"
        "TODO\n\n"
        "## Acceptance Criteria\n\n"
        "TODO\n\n"
        "## Non-Goals\n\n"
        "TODO\n"
    )


def scope_warnings(project_root: Path, scope: list[str]) -> list[str]:
    """Warn about the scope mistakes that are worth catching at open time.

    The gate compares scope entries against paths from ``git diff --name-only``,
    and git lists files, never directories. So an entry naming a directory
    without its trailing slash matches nothing, silently, until the gate refuses
    a change that is in fact correct — the reported failure this exists for.

    **Deliberately bounded.** This catches that mistake, a scope with no
    entries, an entry that names nothing on disk, an empty entry, and a
    ``docs/adr/`` path whose governing decision should be named by a schema-2
    contract. It is not a path validator: entries in unusual forms are left
    alone, because no stated threat requires the tool to police them, and a
    warning that fires on legal input teaches people to ignore warnings.

    Warnings, never refusals: a task may legitimately declare a path it is about
    to create.
    """

    warnings: list[str] = []
    if not scope:
        warnings.append(
            "task declares no scope; no change can land until one is declared"
        )
    for entry in scope:
        if not entry:
            warnings.append("scope entry is empty and matches nothing")
            continue
        if entry == "docs/adr" or entry.startswith("docs/adr/"):
            warnings.append(
                f"scope entry {entry!r} lies under docs/adr/; once written, the "
                "contract should name in decisions (a schema = 2 field) the "
                "decisions the task serves"
            )
        target = project_root / entry.rstrip("/")
        if not entry.endswith("/") and target.is_dir():
            warnings.append(
                f"scope entry {entry!r} names a directory but has no trailing "
                f"slash, so it matches nothing — did you mean {entry + '/'!r}?"
            )
        elif not target.exists():
            warnings.append(
                f"scope entry {entry!r} matches no path in the working tree"
            )
    return warnings


def open_task(
    project_root: Path,
    title: str | None,
    scope: list[str],
    *,
    contract_file: Path | None = None,
) -> OpenedTask:
    """Create a task contract and its opened record.

    The contract is the template *title* and *scope* describe, or the text
    of *contract_file* — a contract already written, whose header ``id`` is
    set to the assigned task id. Either way the `opened` record pins the
    contract's hash, the sha256 of the exact text written (ADR-0018
    decision 1), so a contract supplied through *contract_file* is read and
    validated before the journal is touched.
    """

    provided: tuple[str, str, tuple[str, ...]] | None = None
    if contract_file is None:
        if not title:
            raise TaskOpenError("task title must not be empty")
    else:
        provided = _read_provided_contract(contract_file)
    root = journal_root(project_root)
    metadata_directory = root.parent
    if metadata_directory.is_symlink():
        raise TaskOpenError(
            f"refusing to write through a symlink: {metadata_directory}"
        )
    if root.is_symlink():
        raise TaskOpenError(f"refusing to write through a symlink: {root}")
    if root.exists() and not root.is_dir():
        raise TaskOpenError(f"journal path is not a directory: {root}")
    root.mkdir(parents=True, exist_ok=True)
    task_id = next_task_id(root)
    try:
        validate_task_id(task_id)
    except JournalRecordError as error:
        raise TaskOpenError(str(error)) from error
    tasks_directory = root / "tasks"
    tasks_directory.mkdir(exist_ok=True)
    task_directory = root / "tasks" / task_id
    if task_directory.exists() or task_directory.is_symlink():
        raise TaskOpenError(f"task directory already exists: {task_directory}")
    staging_root = Path(tempfile.mkdtemp(prefix=f".{task_id}-", dir=root))
    staged_task_directory = staging_root / "tasks" / task_id
    staged_contract_path = staged_task_directory / "contract.md"
    try:
        if provided is None:
            contract_text = _contract_content(task_id, cast(str, title), scope)
            declared_scope = tuple(scope)
            replaced_id = None
        else:
            provided_text, provided_id, declared_scope = provided
            contract_text = _retarget_contract_id(provided_text, task_id)
            replaced_id = provided_id if provided_id != task_id else None
        contract_hash = contract_sha256(
            contract_text.encode("utf-8"), str(staged_contract_path)
        )
        staged_task_directory.mkdir(parents=True)
        with staged_contract_path.open(
            "x", encoding="utf-8", newline="\n"
        ) as staged_contract_file:
            staged_contract_file.write(contract_text)
        staged_record_path = write_record(
            staging_root,
            task_id,
            create_opened_record(task_id, __version__, contract=contract_hash),
        )
        if task_directory.exists() or task_directory.is_symlink():
            raise TaskOpenError(f"task directory already exists: {task_directory}")
        staged_task_directory.rename(task_directory)
        # Confirm the postcondition rather than assume it: an adopter reported a
        # task directory created inside a sandboxed session that the operator's
        # own account could not read, while open reported success.
        for written in (
            task_directory / "contract.md",
            task_directory / "records" / staged_record_path.name,
        ):
            try:
                with written.open("rb") as handle:
                    handle.read(1)
            except OSError as error:
                raise TaskOpenError(
                    f"created {written} but cannot read it back: {error}"
                ) from error
    except (OSError, ValueError, JournalRecordError) as error:
        raise TaskOpenError(f"could not create task {task_id}: {error}") from error
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    record_path = task_directory / staged_record_path.relative_to(staged_task_directory)
    return OpenedTask(
        task_id,
        task_directory / "contract.md",
        record_path,
        scope=declared_scope,
        replaced_id=replaced_id,
    )
