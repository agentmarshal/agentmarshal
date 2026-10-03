"""Health checks for AgentMarshal project onboarding."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from agentmarshal.journal.actors import SOURCE_GIT_IDENTITY, resolve_recorded_by
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.placement import PlacementError, resolve_placement
from agentmarshal.journal.review import ReviewLaunchError, _reviewer_command
from agentmarshal.journal.status import TaskStatusError, list_task_statuses
from agentmarshal.journal.status_view import print_paths
from agentmarshal.localstate import LocalState, LocalStateError, local_state
from agentmarshal.process_log import read_events
from agentmarshal.project import (
    GitNotAvailableError,
    find_git_root,
    find_project_root,
    project_file_path,
    read_project_file,
)
from agentmarshal.settings import (
    CHANGES_REQUIRED_THRESHOLD_KEY,
    FINDING_CLASSES_KEY,
    REQUIRE_AGREEMENT_KEY,
    ProjectSettingsError,
    changes_required_threshold,
    finding_classes,
    require_agreement,
)
from agentmarshal.steps import format_overdue, open_steps, step_events_by_task

ExecutableResolver = Callable[[str], str | None]

#: The floor local state's ``git rev-parse --path-format=absolute``
#: sets — the flag git learned at 2.31.
MINIMUM_GIT_VERSION = (2, 31)
MINIMUM_GIT_VERSION_TEXT = ".".join(str(part) for part in MINIMUM_GIT_VERSION)

#: The first dotted number ``git --version`` names — the version
#: itself, the platform suffix (``.windows.1``, ``(Apple Git-…)``)
#: playing no part.
_GIT_VERSION_OUTPUT = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


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
    version = _git_version(result.stdout)
    if version is None:
        return (
            False,
            "cannot read the installed git version; local state needs git "
            f"{MINIMUM_GIT_VERSION_TEXT} or newer for git rev-parse "
            "--path-format=absolute — upgrade git and try again",
        )
    if version[:2] < MINIMUM_GIT_VERSION:
        return (
            False,
            f"git {_version_text(version)} is older than "
            f"{MINIMUM_GIT_VERSION_TEXT}, the minimum local state needs for "
            "git rev-parse --path-format=absolute; upgrade git and try again",
        )
    return (
        True,
        f"git executable is available (git {_version_text(version)}, "
        f"and local state needs {MINIMUM_GIT_VERSION_TEXT} or newer)",
    )


def _git_version(output: str) -> tuple[int, int, int] | None:
    """The version ``git --version`` reports, or ``None`` when it names none.

    The first dotted number is the version — ``git version
    2.39.2.windows.1`` reads as 2.39.2, a platform suffix playing no
    part, and a missing patch level reads as zero.
    """

    match = _GIT_VERSION_OUTPUT.search(output)
    if match is None:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)) if match.group(3) else 0,
    )


def _version_text(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


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


def _check_project_setting(
    start: Path, key: str, read: Callable[[Path], object]
) -> tuple[bool, str]:
    # One check per key: a malformed setting is reported as a failed check
    # of its own, naming the key and what it expects, rather than folding
    # every setting into one result.
    project_root, discovery_error = _find_project_root(start)
    if discovery_error is not None:
        return False, discovery_error
    assert project_root is not None
    try:
        value = read(project_root)
    except ProjectSettingsError as error:
        return False, str(error)
    except (OSError, ValueError) as error:
        path = project_file_path(project_root)
        return False, f"cannot parse {path}; repair the project file ({error})"
    return True, f"{key}: {value!r}"


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
            f"project setting {FINDING_CLASSES_KEY}",
            lambda: _check_project_setting(
                search_start, FINDING_CLASSES_KEY, finding_classes
            ),
        ),
        DoctorCheck(
            f"project setting {CHANGES_REQUIRED_THRESHOLD_KEY}",
            lambda: _check_project_setting(
                search_start,
                CHANGES_REQUIRED_THRESHOLD_KEY,
                changes_required_threshold,
            ),
        ),
        DoctorCheck(
            f"project setting {REQUIRE_AGREEMENT_KEY}",
            lambda: _check_project_setting(
                search_start, REQUIRE_AGREEMENT_KEY, require_agreement
            ),
        ),
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


def _report_locations_and_steps(
    start: Path, stderr: TextIO, now: datetime | None
) -> None:
    """Print the paths in use and the overdue steps, as a report.

    ADR-0014 decisions 9 — as amended — and 13, the ``doctor`` half of
    what ``status`` already does: the journal, the process log and the
    local state print on *stderr* through the same
    ``status_view.print_paths`` call, one line each and escaped like
    other displayed text, and every overdue step across the project's
    tasks prints one line naming its task. Nothing here is a check: an
    overdue step, an unreadable log and an unresolvable path are named,
    never a failure — the exit status stays the checks'.
    """

    project_root, discovery_error = _find_project_root(start)
    placement = None
    placement_reason: str | None = discovery_error
    if project_root is not None:
        try:
            placement = resolve_placement(project_root)
        except PlacementError as error:
            placement_reason = str(error)
    if placement is None:
        reason = escape_for_display(placement_reason or "no project found")
        print(f"journal: unavailable ({reason})", file=stderr)
        print(f"process log: unavailable ({reason})", file=stderr)
        print(f"local state: unavailable ({reason})", file=stderr)
        return
    state: LocalState | None = None
    state_error: str | None = None
    try:
        state = local_state(placement)
    except LocalStateError as error:
        state_error = str(error)
    print_paths(placement.journal_root, state, state_error, stderr)
    _report_overdue_steps(placement.journal_root, state, stderr, now)


def _report_overdue_steps(
    journal_root: Path,
    state: LocalState | None,
    stderr: TextIO,
    now: datetime | None,
) -> None:
    """Print one line per overdue step across the project's tasks.

    Each line carries the task — the report crosses every task, so the
    step id alone would not say whose step is late — the step id, the
    activity, the deadline and how long past it the step is, and says
    it comes from this machine's process log; the whole line is escaped
    like other displayed text. The log is read once and its step events
    grouped under their task once, so each task's ``open_steps`` call
    scans only its own slice; the moment taken as now is taken once and
    is injectable, so a test decides what has passed. A log that cannot
    be read, a journal whose tasks cannot be listed and a local state
    that did not resolve are named, not failures.
    """

    if state is None:
        # The paths lines already named it unavailable with the reason.
        return
    try:
        tasks = list_task_statuses(journal_root)
    except (OSError, TaskStatusError, ValueError) as error:
        print(
            "doctor: cannot list the project's tasks "
            f"({escape_for_display(str(error))}); "
            "their steps read as none",
            file=stderr,
        )
        return
    events = _read_process_events(state, stderr)
    events_by_task = step_events_by_task(events)
    moment = now if now is not None else datetime.now(UTC)
    for task in tasks:
        for step in open_steps(
            task.task_id,
            task.records,
            events_by_task.get(task.task_id, ()),
            now=moment,
        ):
            if step.overdue_by is None:
                continue
            print(
                escape_for_display(
                    "Overdue step (this machine's process log): "
                    f"task={task.task_id} step={step.step} "
                    f"activity={step.activity} deadline={step.deadline} "
                    f"past={format_overdue(step.overdue_by)}"
                ),
                file=stderr,
            )


def _read_process_events(state: LocalState, stderr: TextIO) -> list[dict[str, object]]:
    """Read the process log's events, naming a log that cannot be read.

    A missing ``log/`` directory is no error — ``read_events`` already
    reads it as empty. A log that exists but cannot be read — a
    permission denial, a file where the directory should be — is named
    and reads as no steps rather than failing the run.
    """

    try:
        if state.log.exists() and not state.log.is_dir():
            reason = "not a directory"
        else:
            return read_events(state)
    except OSError as error:
        reason = error.strerror or str(error)
    print(
        f"doctor: cannot read the process log "
        f"{escape_for_display(str(state.log))} ({reason}); "
        "its steps read as none",
        file=stderr,
    )
    return []


def run_doctor(
    start: Path | None = None,
    resolver: ExecutableResolver = shutil.which,
    *,
    stderr: TextIO | None = None,
    now: datetime | None = None,
) -> Sequence[DoctorResult]:
    """Run onboarding health checks without changing project state.

    Besides the checks' results, the run prints to *stderr* — the real
    stderr by default — the paths of the journal, the process log and
    the local state in use and a report of every overdue step across
    the project's tasks; neither is a check and neither can make the
    command fail.
    """

    search_start = Path.cwd() if start is None else start
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
    report_stderr = sys.stderr if stderr is None else stderr
    try:
        _report_locations_and_steps(search_start, report_stderr, now)
    except Exception as error:
        # The report is no check: whatever goes wrong in it is named on
        # stderr rather than failing the command.
        print(
            f"doctor: cannot report paths and overdue steps "
            f"({escape_for_display(str(error))})",
            file=report_stderr,
        )
    return tuple(results)
