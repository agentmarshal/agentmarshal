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

    @property
    def evidence_line(self) -> str:
        """Label evidence with the regime that produced it."""

        return f"Placement: {self.kind}"

    @property
    def advisory_notice(self) -> str | None:
        """State the authority boundary for sidecar gate evidence."""

        if not self.is_sidecar:
            return None
        return "Sidecar checks are advisory and decide no merge."


def _sidecar_host(project_root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise PlacementError(
            f"sidecar project {project_file_path(project_root)} has no valid host path"
        )
    host = Path(value).expanduser()
    # A relative host is resolved against the project, not the process working
    # directory: init always writes an absolute path, but a hand-edited
    # project.json is the supported operator surface for this setting, and a
    # host that meant different repositories from different subdirectories
    # would be a trap.
    if not host.is_absolute():
        host = project_root / host
    return host.resolve()


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
