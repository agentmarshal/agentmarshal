"""Read-only launcher for trusted task reviews."""

from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import cast

# The allowed verdicts have one definition, in records.py, which validation
# uses. The prompt renders that same set so it cannot drift from what the
# record layer will accept. (Module-private today; worth making public the
# next time records.py is opened.)
from agentmarshal.journal.records import _REVIEW_VERDICTS as REVIEW_VERDICTS
from agentmarshal.journal.status import TaskStatusError, load_task_status
from agentmarshal.journal.submit_review import (
    ReviewSubmitError,
    SubmittedReview,
    submit_review,
)

_VERDICT_BEGIN = "AGENTMARSHAL_VERDICT_BEGIN"
_VERDICT_END = "AGENTMARSHAL_VERDICT_END"
_VERDICT_REQUIRED = {"reviewed_commit", "verdict", "findings"}
# advisory_findings is in the record schema and create_review_record accepts it;
# accepting it here is what makes it reachable through the protocol at all.
_VERDICT_OPTIONAL = {"advisory_findings"}


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

    verdicts = ", ".join(sorted(REVIEW_VERDICTS))
    return f"""You are a read-only code reviewer. Review the supplied task contract
and diff.
Do not modify files. Your reviewed commit is {commit}.

At the end, print exactly one JSON object between lines containing exactly
{_VERDICT_BEGIN} and {_VERDICT_END}. The object must contain:
- reviewed_commit: the exact reviewed commit SHA
- verdict: exactly one of: {verdicts}
- findings: an array of unique finding-id strings; empty only for "approved",
  and non-empty for every other verdict
and may additionally contain:
- advisory_findings: an array of unique non-blocking finding-id strings,
  disjoint from findings; allowed with any verdict, including "approved"

No other key is accepted.

Task contract:
{contract}

Diff:
{diff}
"""


def _reviewer_command(model: str, prompt_file: Path) -> list[str]:
    """Build the reviewer command from ``AGENTMARSHAL_REVIEWER_CMD``.

    AgentMarshal is model-agnostic and bundles no reviewer: the operator
    supplies the command that runs their reviewer of choice. It receives the
    review prompt on stdin and must print the machine-verdict block.
    Placeholders ``{model}`` and ``{prompt_file}`` are substituted.
    """

    template_text = os.environ.get("AGENTMARSHAL_REVIEWER_CMD")
    if template_text is None:
        raise ReviewLaunchError(
            "no reviewer command configured: set AGENTMARSHAL_REVIEWER_CMD to the "
            "command that runs your reviewer (AgentMarshal bundles none — it is "
            "model-agnostic). The command reads the prompt on stdin and prints the "
            "machine-verdict block; placeholders {model} and {prompt_file} are "
            "substituted. Example (Codex): "
            "'codex exec --sandbox read-only --model {model} -'. "
            "Alternatively, record a verdict directly with `agentmarshal "
            "submit-review`."
        )
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


def _run_reviewer(command: list[str], snapshot: Path, prompt: str) -> str:
    """Execute the reviewer adapter against the metadata-free snapshot.

    Process-level isolation belongs to the reviewer command's own vendor
    sandbox (ADR-0001; a Codex command, for example, passes
    ``--sandbox read-only``). The
    launcher's own guarantee is the snapshot: a plain copy of the
    reviewed tree with no repository metadata, so nothing the reviewer
    writes through it reaches the repository. ``AGENTMARSHAL_REVIEWER_CMD``
    is a test/ops seam; whoever configures it owns that command's
    isolation.
    """

    try:
        result = subprocess.run(
            command,
            cwd=snapshot,
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


def _preserve_output(output: str) -> Path:
    """Write a rejected reviewer's raw output where the caller can still read it.

    A verdict that fails validation used to take the whole run with it: the
    launcher prints only the record path, so the analysis the reviewer was paid
    to produce had nowhere to survive. The file is deliberately not cleaned up —
    it exists because the run failed, and removing it is the caller's decision.
    """

    descriptor, name = tempfile.mkstemp(
        prefix="agentmarshal-rejected-verdict-", suffix=".txt"
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(output)
    return Path(name)


def _reject(output: str, reason: str) -> ReviewLaunchError:
    """Build a rejection that names where the reviewer's raw output was kept."""

    try:
        kept = _preserve_output(output)
    except OSError as error:  # pragma: no cover - preservation is best effort
        return ReviewLaunchError(f"{reason} (raw output could not be kept: {error})")
    return ReviewLaunchError(f"{reason}; reviewer output kept at {kept}")


def _parse_verdict(output: str) -> tuple[str, str, list[str], list[str]]:
    lines = output.splitlines()
    begins = [index for index, line in enumerate(lines) if line == _VERDICT_BEGIN]
    ends = [index for index, line in enumerate(lines) if line == _VERDICT_END]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        raise _reject(output, "reviewer output has invalid verdict sentinels")
    try:
        verdict_data = json.loads("\n".join(lines[begins[0] + 1 : ends[0]]))
    except json.JSONDecodeError as error:
        raise _reject(output, f"reviewer verdict is not valid JSON: {error}") from error
    if not isinstance(verdict_data, dict):
        raise _reject(output, "reviewer verdict must be a JSON object")
    keys = set(verdict_data)
    missing = _VERDICT_REQUIRED - keys
    if missing:
        raise _reject(
            output,
            "reviewer verdict is missing required field(s): "
            + ", ".join(sorted(missing)),
        )
    # An unknown key is still refused — a verdict we do not understand must not
    # be recorded — but the message names it, instead of reporting a shape
    # failure the reviewer cannot act on.
    unknown = keys - _VERDICT_REQUIRED - _VERDICT_OPTIONAL
    if unknown:
        raise _reject(
            output,
            "reviewer verdict has unsupported field(s): " + ", ".join(sorted(unknown)),
        )
    reviewed_commit = verdict_data["reviewed_commit"]
    verdict = verdict_data["verdict"]
    findings = verdict_data["findings"]
    advisory = verdict_data.get("advisory_findings", [])
    if not isinstance(reviewed_commit, str) or not isinstance(verdict, str):
        raise _reject(output, "reviewer verdict fields must be strings")
    for name, value in (("findings", findings), ("advisory_findings", advisory)):
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise _reject(
                output, f"reviewer verdict {name} must be an array of strings"
            )
    return (
        reviewed_commit,
        verdict,
        cast(list[str], findings),
        cast(list[str], advisory),
    )


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

    review_result: tuple[str, str, list[str], list[str]]
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
            _reviewer_command(reviewer_model, prompt_file),
            snapshot,
            prompt,
        )
        reviewed_commit, verdict, findings, advisory = _parse_verdict(output)
        if reviewed_commit != resolved_commit:
            raise _reject(
                output, "reviewer verdict reviewed_commit does not match commit"
            )
        review_result = reviewed_commit, verdict, findings, advisory
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
            review_result[3] or None,
        )
    except ReviewSubmitError as error:
        raise ReviewLaunchError(str(error)) from error
