"""Trusted recording path for task review verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.artifacts import write_artifact
from agentmarshal.journal.records import (
    JournalRecordError,
    create_review_record,
    generate_ulid,
    validate_record_for_write,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status


class ReviewSubmitError(Exception):
    """Raised when a review verdict cannot be recorded."""

    def __init__(self, message: str, *, artifact_ref: str | None = None) -> None:
        super().__init__(message)
        self.artifact_ref = artifact_ref


@dataclass(frozen=True)
class SubmittedReview:
    """A successfully recorded review and its optional durable prose pin."""

    record_path: Path
    artifact_ref: str | None = None


def submit_review(
    journal_root: Path,
    task_id: str,
    reviewed_commit: str | None,
    verdict: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    findings: list[str],
    advisory_findings: list[str] | None = None,
    *,
    reviewed_finding: str | None = None,
    prose: bytes | None = None,
) -> SubmittedReview:
    """Validate and record a review against an opened task."""

    try:
        load_task_status(journal_root, task_id)
        record = create_review_record(
            task_id,
            __version__,
            reviewed_commit,
            verdict,
            reviewer_role,
            reviewer_vendor,
            reviewer_model,
            reviewer_email,
            findings,
            reviewed_finding=reviewed_finding,
            advisory_findings=advisory_findings,
        )
        if prose is None:
            return SubmittedReview(write_record(journal_root, task_id, record))

        record_id = generate_ulid()
        validate_record_for_write(journal_root, task_id, record, record_id=record_id)
        pin = write_artifact(journal_root, task_id, f"{record_id}-review.md", prose)
        record["artifacts"] = [pin]
        try:
            record_path = write_record(
                journal_root, task_id, record, record_id=record_id
            )
        except (JournalRecordError, OSError, ValueError) as error:
            raise ReviewSubmitError(
                f"{error}; reviewer prose artifact left at {pin['ref']}",
                artifact_ref=pin["ref"],
            ) from error
        return SubmittedReview(
            record_path,
            artifact_ref=pin["ref"],
        )
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReviewSubmitError(str(error)) from error
