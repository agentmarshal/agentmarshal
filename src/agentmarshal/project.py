"""Project discovery and initialization helpers."""

from __future__ import annotations

import json
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


def _is_main_git_directory(git_dir: Path) -> bool:
    """Return whether *git_dir* has the required structure of a Git directory."""

    return (
        (git_dir / "HEAD").is_file()
        and (git_dir / "config").is_file()
        and (git_dir / "objects").is_dir()
        and (git_dir / "refs").is_dir()
    )


def _path_from_git_file(git_file: Path, prefix: str = "") -> Path | None:
    """Resolve a path stored in a Git metadata file."""

    try:
        lines = git_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if len(lines) != 1 or not lines[0].startswith(prefix):
        return None

    stored_path = lines[0].removeprefix(prefix)
    if not stored_path:
        return None
    target = Path(stored_path)
    if not target.is_absolute():
        target = git_file.parent / target
    try:
        return target.resolve()
    except OSError:
        return None


def _is_git_repository_marker(git_path: Path) -> bool:
    """Return whether a .git path identifies a usable Git working tree."""

    if git_path.is_dir():
        return _is_main_git_directory(git_path)
    if not git_path.is_file():
        return False

    git_dir = _path_from_git_file(git_path, "gitdir: ")
    if git_dir is None or not (git_dir / "HEAD").is_file():
        return False
    common_dir_file = git_dir / "commondir"
    if not common_dir_file.is_file():
        return False
    common_dir = _path_from_git_file(common_dir_file)
    return common_dir is not None and _is_main_git_directory(common_dir)


def find_git_root(start: Path | None = None) -> Path | None:
    """Find the nearest git repository root."""

    search_start = Path.cwd() if start is None else start
    for candidate in _ancestors_from(search_start):
        git_path = candidate / ".git"
        if _is_git_repository_marker(git_path):
            return candidate
    return None


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
