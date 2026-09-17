"""Health checks for AgentMarshal project onboarding."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.actors import SOURCE_GIT_IDENTITY, resolve_recorded_by
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
    # A precondition is something this tool's guarantees rest on and that only
    # the operator can establish. Unmet, it is reported and does not make the
    # command fail. Carried here rather than as a list of names elsewhere: two
    # copies of one set drift, and renaming a check proved it.
    precondition: bool = False


@dataclass(frozen=True)
class DoctorResult:
    """The result of one onboarding health check."""

    name: str
    ok: bool
    precondition: bool
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


def _check_actor_variable(start: Path) -> tuple[bool, str]:
    # Ask the resolver the records ask, not just the environment: a project may
    # declare its agents in the actors table instead (ADR-0006), and reporting
    # that as unconfigured would be wrong.
    project_root, discovery_error = _find_project_root(start)
    if discovery_error is not None:
        return False, discovery_error
    assert project_root is not None
    resolved = resolve_recorded_by(project_root)
    if resolved is None:
        return (
            False,
            "no actor can be resolved and no git identity is configured; "
            "records will carry no recorder at all",
        )
    actor, source = resolved
    if source == SOURCE_GIT_IDENTITY:
        # Correct for a person writing their own records, and wrong the moment
        # an agent writes one here: this tool cannot tell which project it is
        # in, so it says what will happen rather than calling it a fault.
        return (
            False,
            f"records will name {actor}, the invoking git identity; an agent "
            "writing records here would be indistinguishable from that person, "
            "so declare AGENTMARSHAL_ACTOR in the agent's harness or map the "
            "identity in the project's actors table",
        )
    return True, f"records will name {actor}, resolved from the {source}"


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
    # A project keeps its CI where its provider wants it: under .github for one,
    # a file in the root for another. This repository's own is in the root, and
    # an earlier draft of this check reported it as having no CI at all.
    definitions: tuple[Path, ...] = ()
    for directory in (project_root / ".github" / "workflows", project_root):
        try:
            definitions += tuple(
                path
                for path in directory.iterdir()
                if path.is_file() and path.suffix in {".yaml", ".yml"}
            )
        except OSError:
            continue
    for definition in definitions:
        try:
            content = definition.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        uncommented = "\n".join(
            line for line in content.splitlines() if not line.lstrip().startswith("#")
        )
        if re.search(r"\bagentmarshal\s+validate\b", uncommented):
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
        DoctorCheck(
            "recorded actor",
            lambda: _check_actor_variable(search_start),
            precondition=True,
        ),
        DoctorCheck(
            "reviewer command placeholders",
            _check_reviewer_command,
            precondition=True,
        ),
        DoctorCheck(
            "CI validate definition",
            lambda: _check_validate_ci_definition(search_start),
            precondition=True,
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
        results.append(DoctorResult(check.name, ok, check.precondition, detail))
    return tuple(results)
