"""Trusted recording path for task review verdicts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.artifacts import write_artifact
from agentmarshal.journal.records import (
    JournalRecordError,
    create_review_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status


class ReviewSubmitError(Exception):
    """Raised when a review verdict cannot be recorded."""


@dataclass(frozen=True)
class SubmittedReview:
    """A successfully recorded review, and any temporary reasoning copy.

    ``reviewer_output_path`` is set only when a launcher preserved the
    reviewer's raw output outside the journal for compatibility with the
    rejected-verdict path. Durable prose is pinned by the review record itself.
    """

    record_path: Path
    reviewer_output_path: Path | None = None
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
        # Refuse a record that write_record would refuse before creating its
        # durable artifact: the verdict's shape, and a finding binding that
        # names no finding of this task. write_record validates again after
        # the pin is attached and remains the only record writer.
        validate_record_content(
            f"{record_id}-review.json",
            json.dumps(record),
        )
        if reviewed_finding is not None:
            finding_ids = {
                item["id"]
                for item in read_records(journal_root, task_id)
                if item["record_type"] == "finding"
            }
            if reviewed_finding not in finding_ids:
                raise JournalRecordError(
                    "record field 'reviewed_finding' must name a finding in the "
                    "same task"
                )
        pin = write_artifact(journal_root, task_id, f"{record_id}-review.md", prose)
        record["artifacts"] = [pin]
        return SubmittedReview(
            write_record(journal_root, task_id, record, record_id=record_id),
            artifact_ref=pin["ref"],
        )
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReviewSubmitError(str(error)) from error
