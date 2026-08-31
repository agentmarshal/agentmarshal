"""Report and remove local artifacts for finished journal tasks."""

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


@dataclass(frozen=True)
class WorktreeDisposition:
    """The eligibility decision for one linked worktree."""

    path: Path
    branch: str | None
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
    """List local branches, saying which are checked out anywhere.

    ``%(HEAD)`` marks only the branch checked out in *this* worktree, so
    ``%(worktreepath)`` is read as well: proposal 010 is about executor
    worktrees — the reporting adopter had forty-five — and a branch held by a
    linked worktree must not be offered for deletion.
    """

    output = _run_git(
        project_root,
        [
            "for-each-ref",
            "--format=%(HEAD)%00%(refname:short)%00%(worktreepath)",
            "refs/heads",
        ],
    )
    branches: list[tuple[str, bool]] = []
    for line in output.splitlines():
        fields = line.split("\0")
        if len(fields) != 3 or fields[0] not in {" ", "*"} or not fields[1]:
            raise PruneError("git returned an unparseable local branch name")
        marker, branch, worktree = fields
        branches.append((branch, marker == "*" or bool(worktree)))
    return branches


def _worktrees(project_root: Path) -> list[tuple[Path, str | None]]:
    """List worktree paths and their checked-out local branches."""

    output = _run_git(project_root, ["worktree", "list", "--porcelain"])
    worktrees: list[tuple[Path, str | None]] = []
    for block in output.strip().split("\n\n"):
        fields: dict[str, str] = {}
        flags: set[str] = set()
        for line in block.splitlines():
            key, separator, value = line.partition(" ")
            if separator:
                fields[key] = value
            else:
                flags.add(key)
        path = fields.get("worktree")
        if path is None:
            raise PruneError("git returned an unparseable worktree list")
        branch_ref = fields.get("branch")
        branch = None
        if branch_ref is not None:
            prefix = "refs/heads/"
            if not branch_ref.startswith(prefix) or not branch_ref[len(prefix) :]:
                raise PruneError("git returned an unparseable worktree branch")
            branch = branch_ref[len(prefix) :]
        elif "detached" not in flags and "bare" not in flags:
            raise PruneError("git returned a worktree without a branch or state")
        worktrees.append((Path(path), branch))
    return worktrees


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


def _task_state(journal_root: Path, task_id: str, states: dict[str, str]) -> str:
    if task_id not in states:
        # Absence is asked of the filesystem, not inferred from the text of an
        # error message elsewhere.
        if not (journal_root / "tasks" / task_id).is_dir():
            states[task_id] = "unknown"
        else:
            try:
                states[task_id] = load_task_status(journal_root, task_id).state
            except (TaskStatusError, OSError, ValueError) as error:
                raise PruneError(str(error)) from error
    return states[task_id]


def report_branches(project_root: Path, base: str = "HEAD") -> list[BranchDisposition]:
    """Classify local branches against journal state and commit containment."""

    _run_git(project_root, ["rev-parse", "--verify", f"{base}^{{commit}}"])
    journal_root = project_root / ".agentmarshal" / "journal"
    states: dict[str, str] = {}
    report: list[BranchDisposition] = []
    for branch, current in _local_branches(project_root):
        if current:
            report.append(BranchDisposition(branch, False, "checked out in a worktree"))
            continue
        task_id = _task_from_branch(branch)
        if task_id is None:
            report.append(BranchDisposition(branch, False, "does not name a task"))
            continue
        state = _task_state(journal_root, task_id, states)
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


def report_worktrees(project_root: Path) -> list[WorktreeDisposition]:
    """Classify worktrees against journal state and working-tree cleanliness."""

    journal_root = project_root / ".agentmarshal" / "journal"
    states: dict[str, str] = {}
    report: list[WorktreeDisposition] = []
    worktrees = _worktrees(project_root)
    # git lists the main worktree first, always. Taking the *invoking* directory
    # for it would be wrong precisely where this command is most useful: run
    # from inside a linked worktree — the executor case proposal 010 describes —
    # that reading calls the linked one main and offers the real main worktree
    # for removal.
    main = worktrees[0][0].resolve() if worktrees else None
    # The worktree the command is running in is never eligible either. git
    # removes it without complaint — verified — leaving the caller standing in a
    # directory that no longer exists and the rest of the run failing on it.
    # This is the same rule CR-059 already applies to the current branch.
    current = project_root.resolve()
    for path, branch in worktrees:
        resolved = path.resolve()
        if main is not None and resolved == main:
            report.append(WorktreeDisposition(path, branch, False, "main worktree"))
            continue
        if resolved == current:
            report.append(
                WorktreeDisposition(path, branch, False, "the worktree you are in")
            )
            continue
        if branch is None:
            report.append(
                WorktreeDisposition(path, branch, False, "not on a local branch")
            )
            continue
        task_id = _task_from_branch(branch)
        if task_id is None:
            report.append(
                WorktreeDisposition(path, branch, False, "does not name a task")
            )
            continue
        state = _task_state(journal_root, task_id, states)
        if state != "done":
            report.append(
                WorktreeDisposition(path, branch, False, f"task {task_id} is {state}")
            )
            continue
        # --untracked-files=all overrides status.showUntrackedFiles: a
        # repository configured to hide untracked files would otherwise read as
        # clean, and untracked files are exactly the data that exists nowhere
        # else. A worktree whose directory has gone is reported, not fatal —
        # git lists such entries, and one stale entry must not cost the report.
        try:
            dirty = bool(
                _run_git(path, ["status", "--porcelain", "--untracked-files=all"])
            )
        except PruneError as error:
            report.append(
                WorktreeDisposition(
                    path, branch, False, f"cannot be inspected: {error}"
                )
            )
            continue
        if dirty:
            report.append(
                WorktreeDisposition(
                    path, branch, False, f"task {task_id} is done but worktree is dirty"
                )
            )
            continue
        report.append(
            WorktreeDisposition(path, branch, True, f"task {task_id} is done and clean")
        )
    return report


@dataclass(frozen=True)
class BranchDeletion:
    """What became of one branch the report marked eligible."""

    branch: str
    deleted: bool
    detail: str


@dataclass(frozen=True)
class WorktreeDeletion:
    """What became of one worktree the report marked eligible."""

    path: Path
    removed: bool
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


def delete_worktrees(
    project_root: Path, report: list[WorktreeDisposition]
) -> Iterator[WorktreeDeletion]:
    """Remove eligible worktrees while retaining git's independent guard."""

    for item in report:
        if not item.eligible:
            continue
        try:
            _run_git(project_root, ["worktree", "remove", str(item.path)])
        except PruneError as error:
            yield WorktreeDeletion(item.path, False, str(error))
            continue
        yield WorktreeDeletion(item.path, True, item.reason)
