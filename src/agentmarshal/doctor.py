"""Health checks for AgentMarshal project onboarding."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.review import ReviewLaunchError, _reviewer_command
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


def _check_actor_variable() -> tuple[bool, str]:
    actor = os.environ.get("AGENTMARSHAL_ACTOR", "").strip()
    if actor:
        return True, "AGENTMARSHAL_ACTOR is declared for this session"
    return (
        False,
        "AGENTMARSHAL_ACTOR is unset; records will resolve to the invoking git "
        "identity, so an agent can be conflated with that identity",
    )


def _check_reviewer_command() -> tuple[bool, str]:
    # An unset command is a configuration, not a fault: the quickstart offers
    # the human path for exactly that. What this check can report is a command
    # that is set and will not launch. Its value is never printed — a vendor
    # template often carries a key.
    if os.environ.get("AGENTMARSHAL_REVIEWER_CMD") is None:
        return (
            True,
            "no reviewer command is configured; reviews are recorded by hand "
            "with submit-review",
        )
    try:
        _reviewer_command("doctor-model", Path("doctor-prompt.txt"))
    except ReviewLaunchError:
        return (
            False,
            "reviewer command placeholders do not resolve; a review cannot launch",
        )
    return True, "reviewer command placeholders resolve"


def _check_validate_ci_definition(start: Path) -> tuple[bool, str]:
    project_root, discovery_error = _find_project_root(start)
    if discovery_error is not None:
        return False, discovery_error
    assert project_root is not None
    workflows = project_root / ".github" / "workflows"
    try:
        definitions = tuple(
            path
            for path in workflows.iterdir()
            if path.is_file() and path.suffix in {".yaml", ".yml"}
        )
    except OSError:
        definitions = ()
    for definition in definitions:
        try:
            content = definition.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if re.search(r"\bagentmarshal\s+validate\b", content):
            return (
                True,
                "CI definition invokes agentmarshal validate: "
                f"{definition.relative_to(project_root)}",
            )
    return (
        False,
        "no CI definition invokes agentmarshal validate; journal integrity is "
        "not checked before merge",
    )


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
        DoctorCheck("actor variable", _check_actor_variable),
        DoctorCheck(
            "reviewer command placeholders",
            _check_reviewer_command,
        ),
        DoctorCheck(
            "CI validate definition",
            lambda: _check_validate_ci_definition(search_start),
        ),
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
