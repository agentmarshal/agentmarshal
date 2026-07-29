"""Read-only launcher for trusted task reviews."""

from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
import tarfile
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from agentmarshal.journal.status import TaskStatusError, load_task_status
from agentmarshal.journal.submit_review import (
    ReviewSubmitError,
    SubmittedReview,
    submit_review,
)

_VERDICT_BEGIN = "AGENTMARSHAL_VERDICT_BEGIN"
_VERDICT_END = "AGENTMARSHAL_VERDICT_END"
_VERDICT_FIELDS = {"reviewed_commit", "verdict", "findings"}
_DEFAULT_REVIEWER_COMMANDS: Mapping[str, tuple[str, ...]] = {
    "codex": (
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--model",
        "{model}",
        "-",
    ),
}

# The reviewer runs in a metadata-free snapshot, but a read-only sandbox still
# permits reads, so any inherited variable that points at or reveals the live
# repository lets the reviewer escape the snapshot and inspect the real
# checkout/.git (defeating review-by-SHA). Drop the known leak vectors and,
# below, any variable whose value carries the project-root path. PATH and HOME
# are always kept — the reviewer adapter (e.g. codex) needs them.
_REVIEWER_ENV_DROP_EXACT = frozenset({"PYTHONPATH", "PWD", "OLDPWD", "VIRTUAL_ENV"})
_REVIEWER_ENV_DROP_PREFIX = ("AGENTMARSHAL_", "GIT_")
_REVIEWER_ENV_KEEP = frozenset({"PATH", "HOME"})


def _sanitized_reviewer_env(project_root: Path) -> dict[str, str]:
    """Reviewer-subprocess environment with every handle on the live repo
    removed, so the metadata-free snapshot is a real isolation boundary."""

    leaks = {str(project_root), str(project_root.resolve())}
    sanitized: dict[str, str] = {}
    for name, value in os.environ.items():
        if name in _REVIEWER_ENV_DROP_EXACT:
            continue
        if any(name.startswith(prefix) for prefix in _REVIEWER_ENV_DROP_PREFIX):
            continue
        if name not in _REVIEWER_ENV_KEEP and any(leak in value for leak in leaks):
            continue
        sanitized[name] = value
    return sanitized


class ReviewLaunchError(Exception):
    """Raised when a read-only review cannot be launched or recorded."""


def _run_git(project_root: Path, arguments: list[str]) -> str:
    """Run git and return its standard output, or raise a launcher error."""

    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ReviewLaunchError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _resolve_commit(project_root: Path, commit: str) -> str:
    resolved = _run_git(
        project_root, ["rev-parse", "--verify", f"{commit}^{{commit}}"]
    ).strip()
    if len(resolved) != 40:
        raise ReviewLaunchError(f"commit did not resolve to a full SHA: {commit}")
    return resolved


def _review_prompt(contract: str, diff: str, commit: str) -> str:
    """Build the reviewer prompt with its required machine-verdict protocol."""

    return f"""You are a read-only code reviewer. Review the supplied task contract
and diff.
Do not modify files. Your reviewed commit is {commit}.

At the end, print exactly one JSON object between lines containing exactly
{_VERDICT_BEGIN} and {_VERDICT_END}. The object must contain only:
- reviewed_commit: the exact reviewed commit SHA
- verdict: an allowed AgentMarshal verdict
- findings: an array of unique finding-id strings

Task contract:
{contract}

Diff:
{diff}
"""


def _reviewer_command(vendor: str, model: str, prompt_file: Path) -> list[str]:
    template_text = os.environ.get("AGENTMARSHAL_REVIEWER_CMD")
    if template_text is None:
        template = _DEFAULT_REVIEWER_COMMANDS.get(vendor)
        if template is None:
            raise ReviewLaunchError(
                f"no reviewer adapter configured for vendor: {vendor}"
            )
    else:
        try:
            template = tuple(shlex.split(template_text))
        except ValueError as error:
            raise ReviewLaunchError(
                f"invalid AGENTMARSHAL_REVIEWER_CMD: {error}"
            ) from error
        if not template:
            raise ReviewLaunchError("AGENTMARSHAL_REVIEWER_CMD must not be empty")
    replacements = {"model": model, "prompt_file": str(prompt_file)}
    try:
        return [element.format(**replacements) for element in template]
    except (KeyError, ValueError) as error:
        raise ReviewLaunchError(
            "AGENTMARSHAL_REVIEWER_CMD has an invalid placeholder"
        ) from error


def _run_reviewer(
    command: list[str], snapshot: Path, prompt: str, env: Mapping[str, str]
) -> str:
    """Execute the reviewer adapter against the metadata-free snapshot.

    Process-level isolation belongs to the vendor sandbox (ADR-0001; the
    built-in codex adapter passes ``--sandbox read-only``). The
    launcher's own guarantee is the snapshot: a plain copy of the
    reviewed tree with no repository metadata, so nothing the reviewer
    writes through it reaches the repository. ``env`` is the sanitized
    reviewer environment (see ``_sanitized_reviewer_env``): even a
    read-only reviewer must not learn the live repo path through an
    inherited variable, or it could read outside the snapshot.
    ``AGENTMARSHAL_REVIEWER_CMD`` is a test/ops seam; whoever configures it
    owns that command's isolation.
    """

    try:
        result = subprocess.run(
            command,
            cwd=snapshot,
            env=dict(env),
            capture_output=True,
            encoding="utf-8",
            input=prompt,
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run reviewer: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        message = f"reviewer exited with status {result.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise ReviewLaunchError(message)
    return result.stdout


def _parse_verdict(output: str) -> tuple[str, str, list[str]]:
    lines = output.splitlines()
    begins = [index for index, line in enumerate(lines) if line == _VERDICT_BEGIN]
    ends = [index for index, line in enumerate(lines) if line == _VERDICT_END]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise ReviewLaunchError("reviewer output has invalid verdict sentinels")
    try:
        verdict_data = json.loads("\n".join(lines[begins[0] + 1 : ends[0]]))
    except json.JSONDecodeError as error:
        raise ReviewLaunchError("reviewer verdict is not valid JSON") from error
    if not isinstance(verdict_data, dict) or set(verdict_data) != _VERDICT_FIELDS:
        raise ReviewLaunchError(
            "reviewer verdict must contain only the required fields"
        )
    reviewed_commit = verdict_data["reviewed_commit"]
    verdict = verdict_data["verdict"]
    findings = verdict_data["findings"]
    if not isinstance(reviewed_commit, str) or not isinstance(verdict, str):
        raise ReviewLaunchError("reviewer verdict fields must be strings")
    if not isinstance(findings, list) or not all(
        isinstance(item, str) for item in findings
    ):
        raise ReviewLaunchError("reviewer verdict findings must be an array of strings")
    return reviewed_commit, verdict, cast(list[str], findings)


def _extract_snapshot(project_root: Path, commit: str, snapshot: Path) -> None:
    """Materialize the reviewed tree as a plain copy without git metadata.

    ``git archive`` piped into stdlib tar extraction: the snapshot
    contains no ``.git`` entry at all, so the reviewer cannot reach the
    repository's metadata through it, and cleanup is the enclosing
    temporary directory's own removal — there is no worktree
    registration to leak.
    """

    try:
        result = subprocess.run(
            ["git", "archive", "--format=tar", commit],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ReviewLaunchError(f"git archive failed: {detail}")
    snapshot.mkdir()
    try:
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
            archive.extractall(snapshot, filter="data")
    except tarfile.TarError as error:
        # An empty tree archives to a lone pax_global_header, which
        # tarfile rejects; an empty snapshot is then correct. Anything
        # else is a real extraction failure.
        if not _run_git(project_root, ["ls-tree", commit]).strip():
            return
        raise ReviewLaunchError(f"snapshot extraction failed: {error}") from error


def launch_review(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
) -> SubmittedReview:
    """Review an exact commit in a temporary metadata-free snapshot and record it."""

    journal_root = project_root / ".agentmarshal" / "journal"
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise ReviewLaunchError(str(error)) from error
    resolved_commit = _resolve_commit(project_root, commit)
    merge_base = _run_git(project_root, ["merge-base", base, resolved_commit]).strip()
    diff = _run_git(project_root, ["diff", f"{merge_base}..{resolved_commit}"])

    review_result: tuple[str, str, list[str]]
    with tempfile.TemporaryDirectory(
        prefix="agentmarshal-review-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        snapshot = temporary_root / "snapshot"
        prompt_file = temporary_root / "review-prompt.txt"
        _extract_snapshot(project_root, resolved_commit, snapshot)
        try:
            contract = (
                snapshot
                / ".agentmarshal"
                / "journal"
                / "tasks"
                / task.task_id
                / "contract.md"
            ).read_text(encoding="utf-8")
        except OSError as error:
            raise ReviewLaunchError(
                f"cannot read task contract from reviewed commit: {error}"
            ) from error
        prompt = _review_prompt(contract, diff, resolved_commit)
        prompt_file.write_text(prompt, encoding="utf-8")
        output = _run_reviewer(
            _reviewer_command(reviewer_vendor, reviewer_model, prompt_file),
            snapshot,
            prompt,
            _sanitized_reviewer_env(project_root),
        )
        reviewed_commit, verdict, findings = _parse_verdict(output)
        if reviewed_commit != resolved_commit:
            raise ReviewLaunchError(
                "reviewer verdict reviewed_commit does not match commit"
            )
        review_result = reviewed_commit, verdict, findings
    try:
        return submit_review(
            journal_root,
            task_id,
            review_result[0],
            review_result[1],
            reviewer_role,
            reviewer_vendor,
            reviewer_model,
            reviewer_email,
            review_result[2],
        )
    except ReviewSubmitError as error:
        raise ReviewLaunchError(str(error)) from error
