"""Read-only launcher for trusted task reviews."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
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
    "codex": ("codex", "exec", "--model", "{model}", "{prompt_file}"),
}


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


def _run_reviewer(command: list[str], snapshot: Path) -> str:
    """Execute the reviewer adapter; this is the sole non-git subprocess boundary."""

    try:
        result = subprocess.run(
            command,
            cwd=snapshot,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        raise ReviewLaunchError(f"cannot run reviewer: {error}") from error
    if result.returncode != 0:
        raise ReviewLaunchError(f"reviewer exited with status {result.returncode}")
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


def launch_review(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
) -> SubmittedReview:
    """Review an exact commit in a temporary detached worktree and record it."""

    journal_root = project_root / ".agentmarshal" / "journal"
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise ReviewLaunchError(str(error)) from error
    resolved_commit = _resolve_commit(project_root, commit)
    merge_base = _run_git(project_root, ["merge-base", base, resolved_commit]).strip()
    diff = _run_git(project_root, ["diff", f"{merge_base}..{resolved_commit}"])
    contract = (journal_root / "tasks" / task.task_id / "contract.md").read_text(
        encoding="utf-8"
    )

    with tempfile.TemporaryDirectory(
        prefix="agentmarshal-review-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        snapshot = temporary_root / "snapshot"
        prompt_file = temporary_root / "review-prompt.txt"
        snapshot_added = False
        try:
            _run_git(
                project_root,
                ["worktree", "add", "--detach", str(snapshot), resolved_commit],
            )
            snapshot_added = True
            prompt_file.write_text(
                _review_prompt(contract, diff, resolved_commit), encoding="utf-8"
            )
            output = _run_reviewer(
                _reviewer_command(reviewer_vendor, reviewer_model, prompt_file),
                snapshot,
            )
            reviewed_commit, verdict, findings = _parse_verdict(output)
            if reviewed_commit != resolved_commit:
                raise ReviewLaunchError(
                    "reviewer verdict reviewed_commit does not match commit"
                )
            try:
                return submit_review(
                    journal_root,
                    task_id,
                    reviewed_commit,
                    verdict,
                    reviewer_role,
                    reviewer_vendor,
                    reviewer_model,
                    findings,
                )
            except ReviewSubmitError as error:
                raise ReviewLaunchError(str(error)) from error
        finally:
            if snapshot_added:
                _run_git(project_root, ["worktree", "remove", "--force", str(snapshot)])
