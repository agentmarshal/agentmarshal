"""Task opening transaction."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
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


_CONTRACT_ID_KEY = re.compile(r"^[ \t]*(?:id|\"id\"|'id')[ \t]*=")


def _read_provided_contract(contract_file: Path) -> tuple[str, str, tuple[str, ...]]:
    """Read and validate a contract supplied on the command line.

    Returns the contract's text, the id its header declares and its declared
    scope. The header is validated exactly as ``parse_contract_text``
    validates a contract already in the journal — the boundary a malformed
    declaration is refused at, before anything it names is trusted.
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
    return text, header.id, header.scope


def _retarget_contract_id(text: str, task_id: str) -> str:
    """Return *text* with the header's ``id`` set to *task_id*.

    Every other byte is kept: the contract was written first, and the text
    its hash is pinned over should differ from the author's only in the id
    the open assigns. The ``id`` key lives in the header's top-level table,
    so the search stops at the first ``[table]`` line.
    """

    bom = text.startswith("\ufeff")
    lines = (text[1:] if bom else text).splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.strip() == "+++")
    end = next(
        index
        for index, line in enumerate(lines[start + 1 :], start + 1)
        if line.strip() == "+++"
    )
    for index in range(start + 1, end):
        line = lines[index]
        if line.lstrip().startswith("["):
            break
        if _CONTRACT_ID_KEY.match(line):
            ending = (
                "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            )
            lines[index] = f"id = {json.dumps(task_id)}{ending}"
            break
    rewritten = ("\ufeff" if bom else "") + "".join(lines)
    # The header parsed before the rewrite, so this confirms rather than
    # checks: the retargeted contract still parses and now names the task.
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
