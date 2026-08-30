"""Project discovery and initialization helpers."""

from __future__ import annotations

import errno
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

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


class UnsafeProjectPathError(AgentMarshalProjectError):
    """Raised when the project file destination is not safe to write."""


def _ancestors_from(start: Path) -> tuple[Path, ...]:
    current = start.resolve()
    if not current.is_dir():
        current = current.parent
    return (current, *current.parents)


def project_file_path(project_root: Path) -> Path:
    """Return the AgentMarshal project file path for a project root."""

    return project_root / PROJECT_DIR_NAME / PROJECT_FILE_NAME


def find_project_root(
    start: Path | None = None, stop_at: Path | None = None
) -> Path | None:
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
            check=False,
        )
    except OSError as error:
        raise GitNotAvailableError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        return None
    try:
        # git permits non-UTF-8 path bytes. Decoding them here used to raise
        # UnicodeDecodeError out of a function whose contract is a path or None,
        # so callers had to guard the call site. The gate already treats
        # undecodable git output as a controlled refusal; so does this.
        toplevel = result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise GitNotAvailableError(
            f"git reported a repository path that is not valid UTF-8: {error}"
        ) from error
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


_DIR_FD_SUPPORTED = (
    os.open in os.supports_dir_fd
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW")
)


def _create_exclusive(path: Path) -> TextIO:
    """Exclusively create *path* for text writing, refusing symlinks.

    Where the platform supports it (POSIX), the file is created relative
    to a descriptor of its parent opened with ``O_DIRECTORY|O_NOFOLLOW``,
    so the parent cannot be swapped for a symlink between validation and
    creation. Elsewhere (Windows) creation is pathname-based: the caller's
    symlink checks defend against hostile checkout contents, while races
    with concurrently running processes of the same user are outside the
    threat model — they cross no privilege boundary.
    """

    file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if not _DIR_FD_SUPPORTED:
        fd = os.open(path, file_flags, 0o666)
        return os.fdopen(fd, "w", encoding="utf-8", newline="\n")
    try:
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            msg = f"refusing to write through a symlink: {path.parent}"
            raise UnsafeProjectPathError(msg) from error
        raise
    try:
        fd = os.open(path.name, file_flags | os.O_NOFOLLOW, 0o666, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)
    return os.fdopen(fd, "w", encoding="utf-8", newline="\n")


def write_project_file(path: Path, data: JsonObject) -> None:
    """Create the project file as UTF-8 without BOM, LF-terminated.

    ``path`` must be built from a resolved project root. Symlinked
    destinations are refused and the file is created exclusively — on
    dir_fd platforms anchored to a no-follow handle of its parent — so a
    hostile checkout cannot redirect the write outside the repository and
    a concurrent initializer surfaces as ``FileExistsError`` for the
    caller instead of being overwritten. See ``_create_exclusive`` for
    the platform-specific guarantee.
    """

    parent = path.parent
    if parent.is_symlink() or path.is_symlink():
        offender = parent if parent.is_symlink() else path
        msg = f"refusing to write through a symlink: {offender}"
        raise UnsafeProjectPathError(msg)
    if parent.exists() and not parent.is_dir():
        msg = f"project directory path exists and is not a directory: {parent}"
        raise UnsafeProjectPathError(msg)
    parent.mkdir(exist_ok=True)
    resolved_parent = parent.resolve()
    if resolved_parent != parent:
        msg = (
            "project directory resolves outside its expected location: "
            f"{parent} -> {resolved_parent}"
        )
        raise UnsafeProjectPathError(msg)
    content = json.dumps(data, indent=2, sort_keys=True)
    with _create_exclusive(path) as project_file:
        project_file.write(f"{content}\n")


def _assert_readable(path: Path) -> None:
    """Confirm a file we just wrote can be read back.

    An adopter reported a task directory created inside a sandboxed session
    inheriting that sandbox's ownership: the operator's own account could not
    read the journal of the task that had just been created, and the command
    reported success. Writing without checking leaves the caller a path nobody
    can use, so the postcondition is checked rather than assumed.

    A byte is actually read: opening can succeed on a file whose first read
    fails, and readable is the property the caller is being promised.
    """

    try:
        with path.open("rb") as handle:
            handle.read(1)
    except OSError as error:
        raise AgentMarshalProjectError(
            f"wrote {path} but cannot read it back: {error}"
        ) from error


_OUTBOX_README = """# Upstream outbox

Findings about **AgentMarshal itself** go here — one file per finding — and are
sent upstream as a batch.

An adopter on a pinned release never patches the tool locally, so everything
noticed about it has exactly one addressee. Without a place to put it, a finding
settles in a chat log or a commit message and never arrives.

## What belongs here

A finding, not a bug title: what was run, what happened, how often, and what the
workaround cost. Measurements are the evidence — counts, ratios, timings — and
they are what upstream quotes.

## Before sending

**Sanitize at source.** Upstream is public and cannot un-publish. Remove
anything specific to this repository or its clients: names, hostnames, internal
paths, task numbers, excerpts of your own code. Send the finding, not the
context it was found in.

The original stays with you. Upstream publishes a digest of each proposal with a
stated disposition, under a pseudonym for the reporter.

See the upstream project's CONTRIBUTING for the language convention and how to
send a batch.
"""


@dataclass(frozen=True)
class InitializedProject:
    """What ``init`` produced: the project root, and how the outbox fared.

    A named type rather than a tuple, because the outbox carries two facts —
    where it belongs and whether it is there — and a caller reading them
    positionally would not say which is which.
    """

    project_root: Path
    outbox: Path
    outbox_error: str | None

    @property
    def outbox_created(self) -> bool:
        return self.outbox_error is None


def _scaffold_outbox(project_directory: Path) -> tuple[Path, str | None]:
    """Create the upstream outbox, and leave an existing one alone.

    Adopter proposal 012: three adopters invented three layouts for the same
    thing because the convention arrived only by reading the upstream
    repository. ``init`` is the one moment the operator is looking at project
    setup, so the convention arrives with the tool.

    Best effort by design — a project that could not write this directory is
    still an initialized project, and failing here would trade a working setup
    for a convenience.
    """

    outbox = project_directory / "upstream"
    readme = outbox / "README.md"
    try:
        outbox.mkdir(exist_ok=True)
        # An adopter who already wrote their own does not lose it.
        with readme.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(_OUTBOX_README)
    except FileExistsError:
        return outbox, None
    except OSError as error:
        # The reason travels with the failure. A caller that only learned
        # "no outbox" would have to guess between a permission problem, a
        # full disk, and a bug of ours.
        return outbox, str(error)
    return outbox, None


def initialize_project(start: Path | None = None) -> InitializedProject:
    """Initialize AgentMarshal in the containing git repository."""

    search_start = Path.cwd() if start is None else start
    git_root = find_git_root(search_start)
    if git_root is None:
        msg = "AgentMarshal init must be run inside a git repository"
        raise NotGitRepositoryError(msg)

    existing_root = find_project_root(search_start, stop_at=git_root)
    if existing_root is not None:
        raise AlreadyInitializedError(existing_root)

    project_file = project_file_path(git_root)
    try:
        write_project_file(project_file, initial_project_data())
    except FileExistsError as error:
        raise AlreadyInitializedError(git_root) from error
    _assert_readable(project_file)
    outbox, outbox_error = _scaffold_outbox(project_file.parent)
    return InitializedProject(git_root, outbox, outbox_error)
