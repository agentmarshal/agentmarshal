"""Resolve where a journal lives and where it reads repository facts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal.project import (
    GitNotAvailableError,
    find_git_root,
    project_file_path,
    read_project_file,
)


class PlacementError(Exception):
    """Raised when journal placement configuration cannot be used."""


@dataclass(frozen=True)
class Placement:
    """The roots and placement declared by one AgentMarshal project."""

    kind: str
    project_root: Path
    journal_root: Path
    host_root: Path

    @property
    def is_sidecar(self) -> bool:
        return self.kind == "sidecar"


def _sidecar_host(project_root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise PlacementError(
            f"sidecar project {project_file_path(project_root)} has no valid host path"
        )
    return Path(value).expanduser().resolve()


def resolve_placement(project_root: Path, *, require_host: bool = False) -> Placement:
    """Resolve journal and git roots, validating a sidecar host when needed."""

    resolved_project = project_root.resolve()
    project_file = project_file_path(resolved_project)
    try:
        data = read_project_file(project_file)
    except (OSError, ValueError) as error:
        raise PlacementError(
            f"cannot read AgentMarshal project {project_file}: {error}"
        ) from error

    kind = data.get("placement", "embedded")
    journal = resolved_project / ".agentmarshal" / "journal"
    if kind == "embedded":
        return Placement("embedded", resolved_project, journal, resolved_project)
    if kind != "sidecar":
        raise PlacementError(
            f"AgentMarshal project {project_file} has unsupported placement {kind!r}"
        )

    host = _sidecar_host(resolved_project, data.get("host"))
    if require_host:
        if not host.exists():
            raise PlacementError(f"sidecar host {host}: path does not exist")
        if not host.is_dir():
            raise PlacementError(f"sidecar host {host}: path is not a directory")
        try:
            git_root = find_git_root(host)
        except GitNotAvailableError as error:
            raise PlacementError(f"sidecar host {host}: {error}") from error
        if git_root is None:
            raise PlacementError(f"sidecar host {host}: not a git worktree")
        host = git_root
    return Placement("sidecar", resolved_project, journal, host)
