"""Trusted recording path for task review verdicts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.artifacts import write_artifact
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.records import (
    JournalRecordError,
    _project_root_for,
    create_review_record,
    forges_rendered_text,
    generate_ulid,
    validate_record_for_write,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from agentmarshal.project import project_file_path, read_project_file


class ReviewSubmitError(Exception):
    """Raised when a review verdict cannot be recorded."""

    def __init__(self, message: str, *, artifact_ref: str | None = None) -> None:
        super().__init__(message)
        self.artifact_ref = artifact_ref


@dataclass(frozen=True)
class SubmittedReview:
    """A successfully recorded review and its optional durable prose pin.

    ``actor_note`` is the not-a-declared-actor line the command owes the
    operator when ``--actor`` names an id the actors table lacks.
    """

    record_path: Path
    artifact_ref: str | None = None
    actor_note: str | None = None


def reviewer_actor_refusal(actor: str) -> str | None:
    """The refusal an ``--actor`` value earns under the record rule, or None.

    Restates the actor clause of the schema-7 review-field rule
    (records.py) — non-empty after stripping, no forgeable character — so
    a launch refuses before the reviewer is paid for; the refusal names
    the flag, not the field, because what the operator typed was a flag.
    ``forges_rendered_text`` is the record layer's own predicate, so the
    two checks cannot drift on what a forgeable character is.
    """

    if not actor.strip():
        return "--actor must be a non-empty string"
    if forges_rendered_text(actor):
        return "--actor must not contain control characters"
    return None


def reviewer_actor_note(journal_root: Path, actor: str) -> str | None:
    """The "not a declared actor" note an ``--actor`` id earns, or None.

    Declared-ness is tested on the id against the project file's
    ``actors`` keys — an actor is a key of the section, not a value of
    ``_actors_table``, which maps identities to actors and would miss an
    actor declaring no identities. The file consulted is the journal
    repository's, found through the same ``_project_root_for``
    ``write_record`` resolves ``recorded_by`` from; one that cannot be
    read declares nothing, and undeclared is a note, never a refusal.
    """

    try:
        project = read_project_file(project_file_path(_project_root_for(journal_root)))
    except (OSError, ValueError):
        project = {}
    actors = project.get("actors")
    if isinstance(actors, dict) and actor in actors:
        return None
    return f"note: reviewer actor {escape_for_display(actor)} is not a declared actor"


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
    reviewed_contract: str | None = None,
    prose: bytes | None = None,
    reviewer_actor: str | None = None,
) -> SubmittedReview:
    """Validate and record a review against an opened task.

    ``reviewer_actor`` is the declared reviewer actor ``--actor`` names
    (ADR-0018 decision 3): checked against the record rule before
    anything is read or written — a refusal must not leave an artifact
    behind — and carried into the record's `reviewer` object, which the
    minimum-schema derivation stamps 7 for.
    """

    if reviewer_actor is not None:
        refusal = reviewer_actor_refusal(reviewer_actor)
        if refusal is not None:
            raise ReviewSubmitError(refusal)
    try:
        load_task_for_record(journal_root, task_id, "review")
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
            reviewed_contract=reviewed_contract,
            advisory_findings=advisory_findings,
            reviewer_actor=reviewer_actor,
        )
        actor_note = (
            reviewer_actor_note(journal_root, reviewer_actor)
            if reviewer_actor is not None
            else None
        )
        if prose is None:
            return SubmittedReview(
                write_record(journal_root, task_id, record), actor_note=actor_note
            )

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
            actor_note=actor_note,
        )
    except (JournalRecordError, TaskStatusError, OSError, ValueError) as error:
        raise ReviewSubmitError(str(error)) from error
