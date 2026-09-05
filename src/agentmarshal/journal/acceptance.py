"""Trusted recording path for operator acceptance over review findings."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from agentmarshal import __version__
from agentmarshal.journal.records import (
    JournalRecordError,
    create_acceptance_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status


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
        task = load_task_status(journal_root, task_id)
        if task.state != "open":
            raise AcceptanceError(
                f"task {task_id} has a terminal record (state: {task.state})"
            )
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
