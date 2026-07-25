"""Derive the gate's task/commit/base from the current git context.

The gate itself is unchanged; this only supplies its inputs when the
operator (or a later lifecycle skill) omits them, so an invocation at
merge collapses to at most a base override. Every derivation is
fail-closed: an ambiguous context refuses rather than gating a guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.gate import GateError, _resolve_commit, _run_git

# Branch policy encodes the task as ``<class>/CR-NNN-slug`` (classes:
# feat, fix, docs, ci, completion). The task id is the ``CR-NNN`` token.
_TASK_IN_BRANCH = re.compile(r"CR-\d+")


@dataclass(frozen=True)
class GateContext:
    """Concrete gate inputs, whether supplied or derived."""

    task: str
    commit: str
    base: str


def derive_task_from_branch(branch: str) -> str:
    """Extract the ``CR-NNN`` task id encoded in a branch name."""
    match = _TASK_IN_BRANCH.search(branch)
    if match is None:
        raise GateError(
            f"branch {branch!r} does not encode a task id "
            "(expected <class>/CR-NNN-slug); pass --task"
        )
    return match.group(0)


def current_branch(project_root: Path) -> str:
    """Return the checked-out branch name, or refuse on a detached HEAD."""
    try:
        branch = _run_git(
            project_root, ["symbolic-ref", "--quiet", "--short", "HEAD"]
        ).strip()
    except GateError as error:
        raise GateError(
            "HEAD is detached; cannot derive a task from the branch, pass --task"
        ) from error
    if not branch:
        raise GateError("cannot determine the current branch; pass --task")
    return branch


def resolve_default_base(project_root: Path) -> str:
    """Detect the default branch via ``origin/HEAD``, falling back to master."""
    try:
        symbolic = _run_git(
            project_root,
            ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        ).strip()
    except GateError:
        symbolic = ""
    if symbolic:
        # ``origin/master`` -> ``master``; strip only the leading remote.
        return symbolic.split("/", 1)[1] if symbolic.startswith("origin/") else symbolic
    try:
        _resolve_commit(project_root, "master")
    except GateError as error:
        raise GateError(
            "cannot determine the default base branch "
            "(no origin/HEAD and no local master); pass --base"
        ) from error
    return "master"


def derive_gate_context(
    project_root: Path,
    task: str | None,
    commit: str | None,
    base: str | None,
) -> GateContext:
    """Resolve gate inputs, deriving any that were not supplied.

    Explicit values always win; derivation touches only the missing ones,
    so passing every flag never requires being on a branch at all.
    """
    resolved_task = (
        task
        if task is not None
        else derive_task_from_branch(current_branch(project_root))
    )
    resolved_commit = (
        commit if commit is not None else _resolve_commit(project_root, "HEAD")
    )
    resolved_base = base if base is not None else resolve_default_base(project_root)
    return GateContext(resolved_task, resolved_commit, resolved_base)
