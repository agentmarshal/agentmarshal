"""Report and delete merged local branches for finished journal tasks."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.status import TaskStatusError, load_task_status

_TASK_ID = re.compile(r"CR-\d+")


class PruneError(Exception):
    """Raised when branch eligibility cannot be determined safely."""


@dataclass(frozen=True)
class BranchDisposition:
    """The eligibility decision for one local branch."""

    branch: str
    eligible: bool
    reason: str


def _run_git(project_root: Path, arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise PruneError(f"cannot run git: {error}") from error
    try:
        stdout = result.stdout.decode("utf-8")
        stderr = result.stderr.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PruneError(f"git produced non-UTF-8 output: {error}") from error
    if result.returncode != 0:
        detail = stderr.strip() or stdout.strip()
        raise PruneError(f"git {' '.join(arguments)} failed: {detail}")
    return stdout


def _local_branches(project_root: Path) -> list[tuple[str, bool]]:
    output = _run_git(
        project_root,
        ["for-each-ref", "--format=%(HEAD)%00%(refname:short)", "refs/heads"],
    )
    branches: list[tuple[str, bool]] = []
    for line in output.splitlines():
        marker, separator, branch = line.partition("\0")
        if separator != "\0" or marker not in {" ", "*"} or not branch:
            raise PruneError("git returned an unparseable local branch name")
        branches.append((branch, marker == "*"))
    return branches


def _task_from_branch(branch: str) -> str | None:
    task_ids: set[str] = set(_TASK_ID.findall(branch))
    if not task_ids:
        return None
    if len(task_ids) != 1:
        raise PruneError(f"branch {branch!r} names more than one task id")
    return next(iter(task_ids))


def _is_merged(project_root: Path, branch: str, base: str) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                f"refs/heads/{branch}",
                base,
            ],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise PruneError(f"cannot run git: {error}") from error
    if result.returncode in {0, 1}:
        return result.returncode == 0
    try:
        detail = (result.stderr or result.stdout).decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise PruneError(f"git produced non-UTF-8 output: {error}") from error
    raise PruneError(f"git merge-base --is-ancestor failed: {detail}")


def report_branches(project_root: Path, base: str = "HEAD") -> list[BranchDisposition]:
    """Classify local branches against journal state and commit containment."""

    _run_git(project_root, ["rev-parse", "--verify", f"{base}^{{commit}}"])
    journal_root = project_root / ".agentmarshal" / "journal"
    states: dict[str, str] = {}
    report: list[BranchDisposition] = []
    for branch, current in _local_branches(project_root):
        if current:
            report.append(BranchDisposition(branch, False, "currently checked out"))
            continue
        task_id = _task_from_branch(branch)
        if task_id is None:
            report.append(BranchDisposition(branch, False, "does not name a task"))
            continue
        if task_id not in states:
            # Absence is asked of the filesystem, not inferred from the text of
            # an error message: a reworded message elsewhere must not turn a
            # branch of an unknown task into a failure of the whole command.
            if not (journal_root / "tasks" / task_id).is_dir():
                states[task_id] = "unknown"
            else:
                try:
                    states[task_id] = load_task_status(journal_root, task_id).state
                except (TaskStatusError, OSError, ValueError) as error:
                    raise PruneError(str(error)) from error
        state = states[task_id]
        if state != "done":
            report.append(
                BranchDisposition(branch, False, f"task {task_id} is {state}")
            )
            continue
        if not _is_merged(project_root, branch, base):
            report.append(
                BranchDisposition(
                    branch, False, f"task {task_id} is done but not merged"
                )
            )
            continue
        report.append(
            BranchDisposition(branch, True, f"task {task_id} is done and merged")
        )
    return report


@dataclass(frozen=True)
class BranchDeletion:
    """What became of one branch the report marked eligible."""

    branch: str
    deleted: bool
    detail: str


def delete_branches(
    project_root: Path, report: list[BranchDisposition]
) -> Iterator[BranchDeletion]:
    """Delete the branches a prior report marked eligible, without forcing.

    ``git branch -D`` would remove a branch whether or not git considers it
    merged, which would leave this module's containment check as the only thing
    between the operator and lost work — and the point of that check is that it
    is one of two independent ones. So ``-d`` is used and a refusal is reported.

    A refusal means git and this command disagree about containment, which the
    operator needs to see rather than have overridden. It can happen honestly:
    ``-d`` judges against HEAD and its upstream, while ``--base`` may name
    another ref.
    """

    for item in report:
        if not item.eligible:
            continue
        try:
            _run_git(project_root, ["branch", "--delete", "--", item.branch])
        except PruneError as error:
            yield BranchDeletion(item.branch, False, str(error))
            continue
        yield BranchDeletion(item.branch, True, item.reason)
