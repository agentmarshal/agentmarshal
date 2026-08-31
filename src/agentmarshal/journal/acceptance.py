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
    accepted_commit: str,
    accepted_by: str,
    reason: str,
    findings: list[str] | None = None,
) -> Path:
    """Validate and append acceptance of the latest review's findings."""

    try:
        task = load_task_status(journal_root, task_id)
        if task.state != "open":
            raise AcceptanceError(
                f"task {task_id} has a terminal record (state: {task.state})"
            )
        reviews = [
            record
            for record in task.records
            if record.get("record_type") == "review"
            and record.get("reviewed_commit") == accepted_commit
        ]
        latest = reviews[-1] if reviews else None
        if latest is None:
            raise AcceptanceError(
                f"latest review verdict for {accepted_commit} was none "
                "(no review of that exact commit)"
            )
        verdict = latest.get("verdict")
        if verdict == "approved":
            raise AcceptanceError(
                f"latest review verdict for {accepted_commit} was approved; "
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
        )
        return write_record(journal_root, task_id, record)
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise AcceptanceError(str(error)) from error
