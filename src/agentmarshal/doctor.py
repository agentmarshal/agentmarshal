"""Health checks for AgentMarshal project onboarding."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.project import (
    GitNotAvailableError,
    find_git_root,
    find_project_root,
    project_file_path,
    read_project_file,
)

ExecutableResolver = Callable[[str], str | None]


@dataclass(frozen=True)
class DoctorCheck:
    """A named health check and its implementation."""

    name: str
    run: Callable[[], tuple[bool, str]]


@dataclass(frozen=True)
class DoctorResult:
    """The result of one onboarding health check."""

    name: str
    ok: bool
    detail: str


def _check_git_available(resolver: ExecutableResolver) -> tuple[bool, str]:
    executable = resolver("git")
    if executable is None:
        return False, "git executable was not found; install git and try again"
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        return False, f"cannot run git; install or repair git ({error})"
    if result.returncode != 0:
        return False, "git --version failed; install or repair git"
    return True, "git executable is available"


def _check_git_repository(start: Path) -> tuple[bool, str]:
    try:
        git_root = find_git_root(start)
    except (GitNotAvailableError, OSError, RuntimeError, UnicodeError) as error:
        return False, f"cannot determine git repository; {error}"
    if git_root is None:
        return False, "not inside a git repository; run this command from a repository"
    return True, f"git repository root: {git_root}"


def _find_project_root(start: Path) -> tuple[Path | None, str | None]:
    try:
        git_root = find_git_root(start)
        if git_root is None:
            return (
                None,
                "not inside a git repository; run this command from a repository",
            )
        project_root = find_project_root(start, stop_at=git_root)
    except (GitNotAvailableError, OSError, RuntimeError, UnicodeError) as error:
        return None, f"cannot determine project location; {error}"
    if project_root is None:
        return None, "no .agentmarshal/project.json found; run agentmarshal init"
    return project_root, None


def _check_project_initialized(start: Path) -> tuple[bool, str]:
    project_root, error = _find_project_root(start)
    if error is not None:
        return False, error
    assert project_root is not None
    path = project_file_path(project_root)
    try:
        with path.open("r", encoding="utf-8-sig") as project_file:
            project_file.read()
    except OSError as error:
        return False, f"cannot read {path}; repair the project file ({error})"
    return True, f"project file: {project_file_path(project_root)}"


def _check_project_schema(start: Path) -> tuple[bool, str]:
    project_root, discovery_error = _find_project_root(start)
    if discovery_error is not None:
        return False, discovery_error
    assert project_root is not None
    path = project_file_path(project_root)
    try:
        project = read_project_file(path)
    except (OSError, ValueError) as error:
        return False, f"cannot parse {path}; repair the project file ({error})"
    if project.get("schema") != 1:
        return False, f"unsupported project schema in {path}; expected schema 1"
    return True, "project schema 1 is supported"


def doctor_checks(
    start: Path | None = None, resolver: ExecutableResolver = shutil.which
) -> list[DoctorCheck]:
    """Build the data-driven onboarding checks for *start*."""

    search_start = Path.cwd() if start is None else start
    return [
        DoctorCheck("git", lambda: _check_git_available(resolver)),
        DoctorCheck("git repository", lambda: _check_git_repository(search_start)),
        DoctorCheck(
            "project initialized", lambda: _check_project_initialized(search_start)
        ),
        DoctorCheck("project schema", lambda: _check_project_schema(search_start)),
    ]


def run_doctor(
    start: Path | None = None, resolver: ExecutableResolver = shutil.which
) -> Sequence[DoctorResult]:
    """Run onboarding health checks without changing project state."""

    results: list[DoctorResult] = []
    for check in doctor_checks(start, resolver):
        try:
            ok, detail = check.run()
        except Exception as error:
            ok = False
            detail = (
                f"check could not run; verify repository access and retry ({error})"
            )
        results.append(DoctorResult(check.name, ok, detail))
    return tuple(results)
