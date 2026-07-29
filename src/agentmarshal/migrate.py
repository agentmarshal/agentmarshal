"""Migration from the v1 markdown journal to v2 journal evidence."""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.attestation import SOURCE_IMPORTED
from agentmarshal.journal.open_task import _contract_content
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_completed_record,
    create_opened_record,
    create_review_record,
    validate_record_content,
    validate_task_id,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status

_TASK_DIRECTORIES = ("open", "done", "abandoned", "backlog")
_TASK_HEADER_FIELDS = frozenset({"Owner", "Type", "Created", "Status", "Scope"})
_REVIEW_HEADER_FIELDS = frozenset(
    {
        "Task",
        "Reviewer-Role",
        "Reviewer-Vendor",
        "Reviewer-Model",
        "Reviewer-Email",
        "Reviewed-Commit",
        "Verdict",
        "Finding-IDs",
    }
)
_STATUS_STATES = {
    "open": "open",
    "in_review": "open",
    "done": "done",
    "abandoned": "abandoned",
}


class JournalMigrationError(ValueError):
    """Raised when a v1 journal cannot be migrated safely."""


@dataclass(frozen=True)
class V1Task:
    """A parsed v1 task contract."""

    path: Path
    task_id: str
    title: str
    scope: list[str]
    status: str
    headers: dict[str, str]


@dataclass(frozen=True)
class V1Review:
    """A parsed v1 review record."""

    path: Path
    task_id: str
    headers: dict[str, str]
    findings: list[str]
    advisory_findings: list[str]


def _error(path: Path, message: str) -> JournalMigrationError:
    return JournalMigrationError(f"{path}: {message}")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise _error(path, f"could not read file: {error}") from error


def _note(report: list[str] | None, message: str) -> None:
    """Record a lenient-mode default or skip, if a report is being collected."""

    if report is not None:
        report.append(message)


def _parse_header(
    path: Path, text: str, required: frozenset[str], *, lenient: bool = False
) -> tuple[dict[str, str], list[str]]:
    headers: dict[str, str] = {}
    scope: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.startswith("##"):
            break
        if line.startswith("- "):
            if "Scope" not in headers:
                raise _error(path, "scope list appears before Scope header")
            item = line[2:].strip()
            if not item:
                raise _error(path, "scope list contains an empty item")
            scope.append(item)
            index += 1
            continue
        if ":" not in line:
            raise _error(path, "malformed Key: Value header")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or (not value and key != "Scope" and not lenient):
            raise _error(path, "malformed Key: Value header")
        if key in headers:
            raise _error(path, f"duplicate header: {key}")
        headers[key] = value
        index += 1
    missing = required - headers.keys()
    if missing and not lenient:
        raise _error(path, f"missing required header(s): {', '.join(sorted(missing))}")
    return headers, scope


def _parse_task(
    path: Path, *, lenient: bool = False, report: list[str] | None = None
) -> V1Task | None:
    text = _read_text(path)
    lines = text.splitlines()
    title_index, title_line = next(
        (
            (index, line)
            for index, line in enumerate(lines)
            if line.startswith("# CR-") and ":" in line
        ),
        (-1, ""),
    )
    if title_index == -1:
        raise _error(path, "missing task title '# CR-NNN: ...'")
    identifier, title = title_line[2:].split(":", 1)
    task_id = identifier.strip()
    title = title.strip()
    if not title:
        raise _error(path, "task title must not be empty")
    try:
        validate_task_id(task_id)
    except JournalRecordError as error:
        raise _error(path, str(error)) from error
    header_start = title_index + 1
    while header_start < len(lines) and not lines[header_start].strip():
        header_start += 1
    headers, scope = _parse_header(
        path, "\n".join(lines[header_start:]), _TASK_HEADER_FIELDS, lenient=lenient
    )
    status = headers.get("Status")
    if status is None or status not in _STATUS_STATES:
        if lenient:
            _note(
                report,
                f"{path}: skipped task (missing/invalid Status={status!r})",
            )
            return None
        raise _error(path, f"unknown Status: {status}")
    if lenient and "Scope" not in headers:
        _note(report, f"{path}: defaulted empty scope (no Scope header)")
    # A done task's completed commit comes from Merged-Commit or
    # Reviewed-Commit; without either it cannot be migrated, so skip it in
    # lenient mode here rather than abort the whole run during writing.
    if (
        lenient
        and status == "done"
        and not (headers.get("Merged-Commit") or headers.get("Reviewed-Commit"))
    ):
        _note(
            report,
            f"{path}: skipped done task (no Merged-Commit or Reviewed-Commit)",
        )
        return None
    if lenient:
        # Owner/Type/Created are not used in the migrated output, but the
        # contract reports every degradation: note when they are lost so the
        # note count reflects the true source condition.
        ignored = [
            field for field in ("Owner", "Type", "Created") if not headers.get(field)
        ]
        if ignored:
            _note(
                report,
                f"{path}: ignored missing/empty non-essential header(s): "
                f"{', '.join(ignored)}",
            )
    return V1Task(path, task_id, title, scope, status, headers)


def _parse_review(
    path: Path, *, lenient: bool = False, report: list[str] | None = None
) -> V1Review | None:
    headers, _ = _parse_header(
        path, _read_text(path), _REVIEW_HEADER_FIELDS, lenient=lenient
    )

    def _skip(reason: str) -> None:
        _note(report, f"{path}: skipped review ({reason})")

    task_id = headers.get("Task", "")
    try:
        validate_task_id(task_id)
    except JournalRecordError as error:
        if lenient:
            _skip(f"invalid Task id: {error}")
            return None
        raise _error(path, str(error)) from error

    # Reviewer identity and the reviewed commit cannot be fabricated: a
    # review lacking any of them is not a valid attestation and is skipped
    # in lenient mode rather than invented.
    essential_fields = (
        "Verdict",
        "Reviewer-Role",
        "Reviewer-Vendor",
        "Reviewer-Model",
        "Reviewer-Email",
        "Reviewed-Commit",
    )
    # Treat an empty essential value the same as an absent one (a lenient
    # header may carry `Reviewer-Role:` with no value).
    missing_essential = [field for field in essential_fields if not headers.get(field)]
    if missing_essential:
        if lenient:
            _skip(f"missing {', '.join(missing_essential)}")
            return None
        # strict mode already raised in _parse_header; unreachable here.
        raise _error(
            path, f"missing required header(s): {', '.join(missing_essential)}"
        )

    verdict = headers["Verdict"]
    if not headers.get("Finding-IDs"):
        if not lenient:
            raise _error(path, "missing required header(s): Finding-IDs")
        if verdict == "approved":
            findings_value = "none"
            _note(report, f"{path}: defaulted Finding-IDs=none (approved review)")
        else:
            _skip(f"missing Finding-IDs for non-approved verdict {verdict!r}")
            return None
    else:
        findings_value = headers["Finding-IDs"]

    findings = (
        []
        if findings_value == "none"
        else [item.strip() for item in findings_value.split(",")]
    )
    if not all(findings) or len(set(findings)) != len(findings):
        if lenient:
            _skip("Finding-IDs are not unique, non-empty ids or 'none'")
            return None
        raise _error(path, "Finding-IDs must be unique, non-empty ids or 'none'")
    advisory_findings: list[str] = []
    if (verdict == "approved") != (not findings):
        if not lenient:
            raise _error(path, "Verdict and Finding-IDs are inconsistent")
        if verdict == "approved" and findings:
            # Pre-v1 approved-with-findings: those findings were non-blocking
            # (v2 approved requires no blocking findings). Preserve them
            # faithfully as advisory findings (CR-034) rather than skip —
            # no loss, no rewrite of the verdict.
            advisory_findings = findings
            findings = []
            _note(
                report,
                f"{path}: reclassified {len(advisory_findings)} finding(s) as "
                "advisory (approved-with-findings)",
            )
        else:
            # A non-approved verdict with no findings cannot be reconstructed.
            _skip("non-approved verdict with no findings to reconstruct")
            return None
    record = create_review_record(
        task_id,
        __version__,
        headers["Reviewed-Commit"],
        verdict,
        headers["Reviewer-Role"],
        headers["Reviewer-Vendor"],
        headers["Reviewer-Model"],
        headers["Reviewer-Email"],
        findings,
        advisory_findings=advisory_findings,
        source=SOURCE_IMPORTED,
    )
    try:
        validate_record_content(
            "01J00000000000000000000000-review.json", json.dumps(record)
        )
    except JournalRecordError as error:
        if lenient:
            _skip(f"invalid review record: {error}")
            return None
        raise _error(path, str(error)) from error
    return V1Review(path, task_id, headers, findings, advisory_findings)


def _source_files(root: Path, directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise JournalMigrationError(f"{directory}: expected a directory")
    return sorted(path for path in directory.rglob("*.md") if path.is_file())


def _load_source(
    source: Path, *, lenient: bool = False, report: list[str] | None = None
) -> tuple[list[V1Task], list[V1Review]]:
    if not source.is_dir():
        raise JournalMigrationError(f"{source}: source journal is not a directory")
    tasks_directory = source / "tasks"
    if not tasks_directory.is_dir():
        raise JournalMigrationError(f"{tasks_directory}: task directory is missing")
    tasks = [
        task
        for name in _TASK_DIRECTORIES
        for path in _source_files(source, tasks_directory / name)
        if (task := _parse_task(path, lenient=lenient, report=report)) is not None
    ]
    task_ids = [task.task_id for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        duplicate = next(task_id for task_id in task_ids if task_ids.count(task_id) > 1)
        raise JournalMigrationError(f"{source}: duplicate task id: {duplicate}")
    reviews = [
        review
        for path in _source_files(source, source / "reviews")
        if (review := _parse_review(path, lenient=lenient, report=report)) is not None
    ]
    known_tasks = set(task_ids)
    kept_reviews: list[V1Review] = []
    for review in reviews:
        if review.task_id not in known_tasks:
            if lenient:
                _note(
                    report,
                    f"{review.path}: skipped review (references unknown task "
                    f"{review.task_id})",
                )
                continue
            raise _error(
                review.path, f"review references unknown task: {review.task_id}"
            )
        kept_reviews.append(review)
    return tasks, kept_reviews


def _write_contract(target: Path, task: V1Task) -> None:
    task_directory = target / "tasks" / task.task_id
    try:
        task_directory.mkdir(parents=True)
        (task_directory / "contract.md").write_text(
            _contract_content(task.task_id, task.title, task.scope),
            encoding="utf-8",
            newline="\n",
        )
    except OSError as error:
        raise _error(
            task.path, f"could not write migrated contract: {error}"
        ) from error


def _migrate_task(target: Path, task: V1Task, reviews: list[V1Review]) -> None:
    _write_contract(target, task)
    try:
        write_record(
            target,
            task.task_id,
            create_opened_record(task.task_id, __version__, source=SOURCE_IMPORTED),
        )
        for review in reviews:
            headers = review.headers
            write_record(
                target,
                task.task_id,
                create_review_record(
                    task.task_id,
                    __version__,
                    headers["Reviewed-Commit"],
                    headers["Verdict"],
                    headers["Reviewer-Role"],
                    headers["Reviewer-Vendor"],
                    headers["Reviewer-Model"],
                    headers["Reviewer-Email"],
                    review.findings,
                    advisory_findings=review.advisory_findings,
                    source=SOURCE_IMPORTED,
                ),
            )
        if task.status == "done":
            completed_commit = task.headers.get("Merged-Commit") or task.headers.get(
                "Reviewed-Commit"
            )
            if completed_commit is None:
                raise _error(
                    task.path, "done task has no Merged-Commit or Reviewed-Commit"
                )
            write_record(
                target,
                task.task_id,
                create_completed_record(
                    task.task_id,
                    __version__,
                    completed_commit,
                    source=SOURCE_IMPORTED,
                ),
            )
        elif task.status == "abandoned":
            reason = task.headers.get("Reason", "migrated from v1")
            write_record(
                target,
                task.task_id,
                create_abandoned_record(
                    task.task_id, __version__, reason, source=SOURCE_IMPORTED
                ),
            )
        projected = load_task_status(target, task.task_id).state
    except (JournalRecordError, OSError, TaskStatusError, ValueError) as error:
        raise _error(task.path, f"could not migrate task: {error}") from error
    expected = _STATUS_STATES[task.status]
    if projected != expected:
        raise _error(task.path, f"state projection is {projected}, expected {expected}")


def migrate_journal(
    source: Path,
    target: Path,
    *,
    lenient: bool = False,
    report: list[str] | None = None,
) -> list[str]:
    """Convert *source* v1 journal into a new v2 journal at *target*.

    In ``lenient`` mode, tasks/reviews with pre-v1 header deltas are
    defaulted where semantically safe or skipped (never fabricated), and
    each default/skip is appended to *report* if one is provided.
    """

    source = source.resolve()
    target = target.resolve()
    if target.is_relative_to(source):
        raise JournalMigrationError(
            "target journal directory must not be inside the source journal"
        )
    if target.exists() and any(target.iterdir()):
        raise JournalMigrationError(
            f"{target}: target journal already exists and is not empty"
        )
    if target.exists() and not target.is_dir():
        raise JournalMigrationError(f"{target}: target journal is not a directory")
    tasks, reviews = _load_source(source, lenient=lenient, report=report)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f".{target.name}.migration-", dir=target.parent)
        )
    except OSError as error:
        raise JournalMigrationError(
            f"{target}: could not create migration staging directory: {error}"
        ) from error
    try:
        summaries: list[str] = []
        for task in sorted(
            tasks, key=lambda item: int(item.task_id.removeprefix("CR-"))
        ):
            task_reviews = sorted(
                (review for review in reviews if review.task_id == task.task_id),
                key=lambda review: review.path.as_posix(),
            )
            _migrate_task(staging, task, task_reviews)
            state = _STATUS_STATES[task.status]
            summaries.append(f"{task.task_id}: {state} ({len(task_reviews)} review(s))")
        if target.exists():
            target.rmdir()
        staging.replace(target)
    except OSError as error:
        raise JournalMigrationError(
            f"{target}: could not publish migrated journal: {error}"
        ) from error
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return summaries
