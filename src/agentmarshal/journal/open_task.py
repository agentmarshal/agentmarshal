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
