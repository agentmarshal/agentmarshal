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
    """The path of a successfully recorded review."""

    record_path: Path


def submit_review(
    journal_root: Path,
    task_id: str,
    reviewed_commit: str,
    verdict: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    findings: list[str],
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
            findings,
        )
        return SubmittedReview(write_record(journal_root, task_id, record))
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReviewSubmitError(str(error)) from error
