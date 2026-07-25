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
# feat, fix, docs, ci, completion). The whole name must match this shape:
# an anchored parse rejects unsupported classes and ids embedded in a slug,
# so a malformed branch refuses rather than gating the wrong contract.
_BRANCH_TASK = re.compile(r"(?:feat|fix|docs|ci|completion)/(CR-\d+)-\S+")
_ANY_TASK_ID = re.compile(r"CR-\d+")


@dataclass(frozen=True)
class GateContext:
    """Concrete gate inputs, whether supplied or derived."""

    task: str
    commit: str
    base: str


def derive_task_from_branch(branch: str) -> str:
    """Extract the ``CR-NNN`` task id from a ``<class>/CR-NNN-slug`` branch."""
    match = _BRANCH_TASK.fullmatch(branch)
    if match is None:
        raise GateError(
            f"branch {branch!r} does not follow <class>/CR-NNN-slug "
            "(classes: feat, fix, docs, ci, completion); pass --task"
        )
    # A slug that carries a second, different id is ambiguous: refuse rather
    # than silently gating the first one.
    if len({found for found in _ANY_TASK_ID.findall(branch)}) > 1:
        raise GateError(
            f"branch {branch!r} encodes more than one task id; pass --task"
        )
    return match.group(1)


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
        # ``symbolic`` is a resolvable remote-tracking ref (e.g. ``origin/master``);
        # return it as-is. Stripping to a bare ``master`` would break checkouts
        # that track the remote default without a matching local branch.
        _resolve_commit(project_root, symbolic)
        return symbolic
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
