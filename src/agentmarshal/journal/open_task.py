"""Task opening transaction."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
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
    """Return a warning for every scope entry that cannot match a changed path.

    This mirrors what the gate actually compares, which is stricter than asking
    the filesystem whether something exists:

    * the gate matches entries against paths from ``git diff --name-only``, and
      git lists **files**, never directories — so a plain entry naming a
      directory can never match, which is the reported failure;
    * an entry ending in ``/`` matches the exact path with the slash stripped as
      well as everything beneath it, so it is satisfied by a file of that name
      too;
    * git paths are repository-relative and normalised, so an absolute entry,
      one containing ``..``, or one written as ``./x`` cannot match anything the
      gate will ever see, however well it resolves on this machine.

    These are warnings, never refusals: a task may legitimately declare a path
    it is about to create.
    """

    warnings: list[str] = []
    for entry in scope:
        if not entry:
            # An empty entry reaches the contract and matches nothing: the gate
            # compares it as an exact path. Silence here would be the very
            # failure this function exists to prevent.
            warnings.append("scope entry is empty and matches nothing")
            continue
        parts = entry.split("/")
        # Git emits normalised, repository-relative POSIX paths. An entry that
        # is not in that form resolves perfectly well on this machine and still
        # cannot match anything the gate will ever compare against, so the whole
        # family is rejected together rather than case by case.
        # Only forms git can never emit are rejected. A backslash or a space is
        # a legal character in a git path, so neither is a defect here: a
        # warning that cries wolf teaches people to ignore warnings.
        if entry.startswith("/") or "//" in entry or "." in parts or ".." in parts:
            warnings.append(
                f"scope entry {entry!r} is not a normalised repository-relative "
                "path, so it cannot match any changed path the gate sees"
            )
            continue
        base = entry.rstrip("/")
        target = project_root / base
        # git stores a symlink as a link, never as a directory it can descend
        # into, so nothing under a symlinked path is ever emitted as a change.
        # Every component has to be checked, not just the last one: the entry
        # may sit beneath a symlinked ancestor.
        walked = project_root
        symlinked = False
        for part in base.split("/"):
            walked = walked / part
            if walked.is_symlink():
                symlinked = True
                break
        if symlinked:
            warnings.append(
                f"scope entry {entry!r} resolves through a symlink; git never "
                "reports paths beneath one, so it matches nothing"
            )
            continue
        if entry.endswith("/"):
            # A trailing slash matches the slash-stripped path as well as
            # everything under it, so an existing file of that name satisfies it.
            if not target.exists():
                warnings.append(
                    f"scope entry {entry!r} matches no path in the working tree"
                )
            continue
        if target.is_dir():
            warnings.append(
                f"scope entry {entry!r} names a directory but has no trailing "
                f"slash, so it matches nothing — did you mean {entry + '/'!r}?"
            )
        elif not target.is_file():
            warnings.append(
                f"scope entry {entry!r} matches no path in the working tree"
            )
    return warnings


def open_task(project_root: Path, title: str, scope: list[str]) -> OpenedTask:
    """Create a task contract and its opened record."""

    if not title:
        raise TaskOpenError("task title must not be empty")
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
        staged_task_directory.mkdir(parents=True)
        with staged_contract_path.open(
            "x", encoding="utf-8", newline="\n"
        ) as contract_file:
            contract_file.write(_contract_content(task_id, title, scope))
        staged_record_path = write_record(
            staging_root,
            task_id,
            create_opened_record(task_id, __version__),
        )
        if task_directory.exists() or task_directory.is_symlink():
            raise TaskOpenError(f"task directory already exists: {task_directory}")
        staged_task_directory.rename(task_directory)
    except (OSError, ValueError, JournalRecordError) as error:
        raise TaskOpenError(f"could not create task {task_id}: {error}") from error
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    record_path = task_directory / staged_record_path.relative_to(staged_task_directory)
    return OpenedTask(task_id, task_directory / "contract.md", record_path)
