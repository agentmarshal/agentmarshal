"""Project discovery and initialization helpers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import cast

from agentmarshal import __version__

JsonObject = dict[str, object]

PROJECT_DIR_NAME = ".agentmarshal"
PROJECT_FILE_NAME = "project.json"


class AgentMarshalProjectError(Exception):
    """Base class for project setup failures."""


class AlreadyInitializedError(AgentMarshalProjectError):
    """Raised when a project file already exists."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        super().__init__(f"AgentMarshal is already initialized at {project_root}")


class NotGitRepositoryError(AgentMarshalProjectError):
    """Raised when no git repository root can be found."""


class GitNotAvailableError(AgentMarshalProjectError):
    """Raised when the git executable cannot be invoked."""


def _ancestors_from(start: Path) -> tuple[Path, ...]:
    current = start.resolve()
    if not current.is_dir():
        current = current.parent
    return (current, *current.parents)


def project_file_path(project_root: Path) -> Path:
    """Return the AgentMarshal project file path for a project root."""

    return project_root / PROJECT_DIR_NAME / PROJECT_FILE_NAME


def find_project_root(start: Path | None = None, stop_at: Path | None = None) -> Path | None:
    """Find the nearest initialized AgentMarshal project root."""

    search_start = Path.cwd() if start is None else start
    resolved_stop = stop_at.resolve() if stop_at is not None else None
    for candidate in _ancestors_from(search_start):
        if project_file_path(candidate).is_file():
            return candidate
        if resolved_stop is not None and candidate == resolved_stop:
            return None
    return None


def find_git_root(start: Path | None = None) -> Path | None:
    """Find the working-tree root of the containing git repository.

    Detection is delegated to ``git rev-parse``: git itself is the only
    authority on what constitutes a repository (regular layout, separate
    git dir, linked worktree, submodule). A bare repository has no working
    tree and therefore yields ``None``.
    """

    search_start = Path.cwd() if start is None else start
    if not search_start.is_dir():
        search_start = search_start.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(search_start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        raise GitNotAvailableError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        return None
    toplevel = result.stdout.strip()
    if not toplevel:
        return None
    return Path(toplevel).resolve()


def read_project_file(path: Path) -> JsonObject:
    """Read a project file, accepting a UTF-8 BOM if present."""

    with path.open("r", encoding="utf-8-sig") as project_file:
        data = json.load(project_file)
    if not isinstance(data, dict):
        msg = f"AgentMarshal project file must contain a JSON object: {path}"
        raise ValueError(msg)
    return cast(JsonObject, data)


def initial_project_data() -> JsonObject:
    """Build the initial project configuration."""

    return {
        "schema": 1,
        "framework": {
            "version": __version__,
        },
    }


def write_project_file(path: Path, data: JsonObject) -> None:
    """Write a project file as UTF-8 without BOM, LF-terminated."""

    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, sort_keys=True)
    path.write_text(f"{content}\n", encoding="utf-8", newline="\n")


def initialize_project(start: Path | None = None) -> Path:
    """Initialize AgentMarshal in the containing git repository."""

    search_start = Path.cwd() if start is None else start
    git_root = find_git_root(search_start)
    if git_root is None:
        msg = "AgentMarshal init must be run inside a git repository"
        raise NotGitRepositoryError(msg)

    existing_root = find_project_root(search_start, stop_at=git_root)
    if existing_root is not None:
        raise AlreadyInitializedError(existing_root)

    write_project_file(project_file_path(git_root), initial_project_data())
    return git_root
