"""Where the clone's local state lives (ADR-0014 decisions 4 and 5).

The process log, personal extensions, installed dependencies, trust grants,
personal switches and the plan file sit in ``agentmarshal/`` under the git
common directory of the repository that holds the project's journal — shared
by every worktree of that repository, never committed, deleted with the
clone. In a sidecar that is the journal repository's directory, never the
host's: the host is never written (ADR-0008).

Resolving answers "where" and creates nothing; a writer that needs a
directory location creates it explicitly with
:meth:`LocalState.ensure_directory`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.placement import Placement
from agentmarshal.project import GitNotAvailableError, git_common_dir

LOCAL_STATE_DIR_NAME = "agentmarshal"


class LocalStateError(Exception):
    """Raised when local state cannot be located or created."""


@dataclass(frozen=True)
class LocalState:
    """The named locations under one repository's local state root.

    Pure paths: nothing named here exists until a writer creates it.
    """

    root: Path

    @property
    def log(self) -> Path:
        """The process log directory."""

        return self.root / "log"

    @property
    def extensions(self) -> Path:
        """This clone's personal extensions directory."""

        return self.root / "extensions"

    @property
    def deps(self) -> Path:
        """Extension dependencies installed from the lock."""

        return self.root / "deps"

    @property
    def trust_file(self) -> Path:
        """Local run grants."""

        return self.root / "trust.toml"

    @property
    def switches_file(self) -> Path:
        """Personal extension switches."""

        return self.root / "switches.toml"

    @property
    def plan_file(self) -> Path:
        """The plan file (ADR-0022 section 7)."""

        return self.root / "plan.toml"

    def ensure_directory(self, location: Path) -> Path:
        """Create a directory location under this root, with any missing parents.

        The explicit counterpart of resolving: a writer passes one of the
        named locations — the root, ``log``, ``extensions``, ``deps``, or a
        path under them — when it is about to write into it. The location is
        resolved before the check, so a path that only comes under the root
        through ``..`` segments or symlinks is refused, like any other path
        outside the root.
        """

        try:
            root = self.root.resolve()
            target = location.resolve()
        except OSError as error:
            raise LocalStateError(f"cannot resolve {location}: {error}") from error
        if not target.is_relative_to(root):
            raise LocalStateError(
                f"{location}: outside the local state root {self.root}"
            )
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise LocalStateError(f"cannot create {location}: {error}") from error
        return target


def local_state(placement: Placement) -> LocalState:
    """Resolve the project's local state locations; creates nothing.

    The repository asked is the one holding the journal —
    ``placement.project_root`` in every placement, so a sidecar resolves to
    its own git common directory and the host never enters the call.
    """

    worktree = placement.project_root
    try:
        answer = git_common_dir(worktree)
    except GitNotAvailableError as error:
        raise LocalStateError(f"{worktree}: {error}") from error
    if answer.path is None:
        reason = answer.reason or "git gave no reason"
        raise LocalStateError(
            f"{worktree}: git cannot name a common directory: {reason}"
        )
    return LocalState(answer.path / LOCAL_STATE_DIR_NAME)
