"""Trusted recording path for task review verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.records import (
    JournalRecordError,
    create_review_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status


class ReviewSubmitError(Exception):
    """Raised when a review verdict cannot be recorded."""


@dataclass(frozen=True)
class SubmittedReview:
    """A successfully recorded review, and any reasoning kept beside it.

    ``reviewer_output_path`` is set only when a launcher preserved the
    reviewer's raw output — the record itself carries finding ids, never their
    reasoning. It is ``None`` for a review submitted from a verdict the caller
    already had.
    """

    record_path: Path
    reviewer_output_path: Path | None = None


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
        return SubmittedReview(write_record(journal_root, task_id, record))
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReviewSubmitError(str(error)) from error
