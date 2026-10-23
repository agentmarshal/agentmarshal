"""Trusted recording path for operator acceptance."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import cast

from agentmarshal import __version__
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.extensions import (
    ExtensionManifestError,
    read_extension_manifest,
)
from agentmarshal.journal.records import (
    JournalRecordError,
    create_acceptance_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record


class AcceptanceError(Exception):
    """Raised when an acceptance cannot be recorded."""


def accept_findings(
    journal_root: Path,
    task_id: str,
    accepted_commit: str | None,
    accepted_by: str,
    reason: str,
    findings: list[str] | None = None,
    *,
    accepted_finding: str | None = None,
) -> Path:
    """Validate and append acceptance of the latest review's findings."""

    try:
        task = load_task_for_record(journal_root, task_id, "acceptance")
        if (accepted_commit is None) == (accepted_finding is None):
            raise AcceptanceError(
                "acceptance must name exactly one of accepted_commit or "
                "accepted_finding"
            )
        binding_field = (
            "reviewed_finding" if accepted_finding is not None else "reviewed_commit"
        )
        binding = accepted_finding if accepted_finding is not None else accepted_commit
        reviews = [
            record
            for record in task.records
            if record.get("record_type") == "review"
            and record.get(binding_field) == binding
        ]
        latest = reviews[-1] if reviews else None
        if latest is None:
            exact = "finding" if accepted_finding is not None else "commit"
            raise AcceptanceError(
                f"latest review verdict for {binding} was none "
                f"(no review of that exact {exact})"
            )
        verdict = latest.get("verdict")
        if verdict == "approved":
            raise AcceptanceError(
                f"latest review verdict for {binding} was approved; "
                "acceptance requires a non-approving verdict"
            )
        reviewed_findings = cast(list[str], latest["findings"])
        if findings is not None:
            supplied = set(findings)
            reviewed = set(reviewed_findings)
            missing = sorted(reviewed - supplied)
            extra = sorted(supplied - reviewed)
            duplicates = sorted(
                finding for finding in supplied if findings.count(finding) > 1
            )
            if missing or extra or duplicates:
                differences = []
                if missing:
                    differences.append("missing: " + ", ".join(missing))
                if extra:
                    differences.append("extra: " + ", ".join(extra))
                if duplicates:
                    differences.append("duplicated: " + ", ".join(duplicates))
                raise AcceptanceError(
                    "supplied findings differ from the latest review ("
                    + "; ".join(differences)
                    + ")"
                )
        record = create_acceptance_record(
            task_id,
            __version__,
            accepted_commit,
            accepted_by,
            list(reviewed_findings),
            reason,
            accepted_finding=accepted_finding,
        )
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise AcceptanceError(str(error)) from error


def _resolve_commit(project_root: Path, reference: str) -> str:
    """Resolve *reference* to its full commit id in the journal's repository.

    ``rev-parse --verify <rev>^{commit}`` answers both halves of the rule
    at once: what resolves is the full id, and what does not — a rev the
    repository does not hold, or one naming no commit — fails here rather
    than reaching the record's hex rule with a name it cannot take.
    """

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{reference}^{{commit}}"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise AcceptanceError(f"cannot run git: {error}") from error
    resolved = result.stdout.decode("utf-8", errors="replace").strip()
    if result.returncode != 0 or len(resolved) != 40:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        message = (
            f"--commit {escape_for_display(reference)} does not resolve to "
            "a commit in the journal's repository"
        )
        if detail:
            # git's error text is a value the tool did not write — escaped
            # like every displayed string it does not control.
            message += f": {escape_for_display(detail)}"
        raise AcceptanceError(message)
    return resolved


def accept_pause_or_operational(
    journal_root: Path,
    project_root: Path,
    task_id: str,
    commit: str,
    accepted_by: str,
    reason: str,
    *,
    accepted_pause: str | None = None,
    operational: bool = False,
) -> Path:
    """Validate and append a pause or operational acceptance.

    The two commit-bound forms of ADR-0013: ``accepted_pause`` names the
    shared extension whose pause is accepted (decision 5) and
    ``operational`` marks the acceptance of an operational CR (decision
    17). Neither consults the task's reviews — a pause raises no review
    finding and an operational CR has no review — so the task's lifecycle
    admission through ``load_task_for_record`` is the only task-side
    check. A pause acceptance requires the extension's manifest to be
    readable in the journal repository's working tree; a refusal there
    names the extension. Every refusal lands before ``write_record``.
    """

    try:
        load_task_for_record(journal_root, task_id, "acceptance")
        if accepted_pause is not None:
            try:
                read_extension_manifest(project_root, accepted_pause)
            except ExtensionManifestError as error:
                raise AcceptanceError(
                    f"--pause {escape_for_display(accepted_pause)}: "
                    f"{escape_for_display(str(error))}"
                ) from error
        resolved = _resolve_commit(project_root, commit)
        record = create_acceptance_record(
            task_id,
            __version__,
            resolved,
            accepted_by,
            None,
            reason,
            accepted_pause=accepted_pause,
            operational=operational,
        )
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise AcceptanceError(str(error)) from error
