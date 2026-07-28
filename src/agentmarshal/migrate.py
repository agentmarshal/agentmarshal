"""Migration from the v1 markdown journal to v2 journal evidence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile

from agentmarshal import __version__
from agentmarshal.journal.attestation import SOURCE_IMPORTED
from agentmarshal.journal.open_task import _contract_content
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_completed_record,
    create_opened_record,
    create_review_record,
    validate_task_id,
    validate_record_content,
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


def _error(path: Path, message: str) -> JournalMigrationError:
    return JournalMigrationError(f"{path}: {message}")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise _error(path, f"could not read file: {error}") from error


def _parse_header(
    path: Path, text: str, required: frozenset[str]
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
        if not key or (not value and key != "Scope"):
            raise _error(path, "malformed Key: Value header")
        if key in headers:
            raise _error(path, f"duplicate header: {key}")
        headers[key] = value
        index += 1
    missing = required - headers.keys()
    if missing:
        raise _error(path, f"missing required header(s): {', '.join(sorted(missing))}")
    return headers, scope


def _parse_task(path: Path) -> V1Task:
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
        path, "\n".join(lines[header_start:]), _TASK_HEADER_FIELDS
    )
    status = headers["Status"]
    if status not in _STATUS_STATES:
        raise _error(path, f"unknown Status: {status}")
    return V1Task(path, task_id, title, scope, status, headers)


def _parse_review(path: Path) -> V1Review:
    headers, _ = _parse_header(path, _read_text(path), _REVIEW_HEADER_FIELDS)
    task_id = headers["Task"]
    try:
        validate_task_id(task_id)
    except JournalRecordError as error:
        raise _error(path, str(error)) from error
    findings_value = headers["Finding-IDs"]
    findings = (
        []
        if findings_value == "none"
        else [item.strip() for item in findings_value.split(",")]
    )
    if not all(findings) or len(set(findings)) != len(findings):
        raise _error(path, "Finding-IDs must be unique, non-empty ids or 'none'")
    verdict = headers["Verdict"]
    if (verdict == "approved") != (not findings):
        raise _error(path, "Verdict and Finding-IDs are inconsistent")
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
        source=SOURCE_IMPORTED,
    )
    try:
        validate_record_content(
            "01J00000000000000000000000-review.json", json.dumps(record)
        )
    except JournalRecordError as error:
        raise _error(path, str(error)) from error
    return V1Review(path, task_id, headers)


def _source_files(root: Path, directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise JournalMigrationError(f"{directory}: expected a directory")
    return sorted(path for path in directory.rglob("*.md") if path.is_file())


def _load_source(source: Path) -> tuple[list[V1Task], list[V1Review]]:
    if not source.is_dir():
        raise JournalMigrationError(f"{source}: source journal is not a directory")
    tasks_directory = source / "tasks"
    if not tasks_directory.is_dir():
        raise JournalMigrationError(f"{tasks_directory}: task directory is missing")
    tasks = [
        _parse_task(path)
        for name in _TASK_DIRECTORIES
        for path in _source_files(source, tasks_directory / name)
    ]
    task_ids = [task.task_id for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        duplicate = next(task_id for task_id in task_ids if task_ids.count(task_id) > 1)
        raise JournalMigrationError(f"{source}: duplicate task id: {duplicate}")
    reviews = [
        _parse_review(path) for path in _source_files(source, source / "reviews")
    ]
    known_tasks = set(task_ids)
    for review in reviews:
        if review.task_id not in known_tasks:
            raise _error(
                review.path, f"review references unknown task: {review.task_id}"
            )
    return tasks, reviews


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


def _review_findings(review: V1Review) -> list[str]:
    value = review.headers["Finding-IDs"]
    return [] if value == "none" else [item.strip() for item in value.split(",")]


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
                    _review_findings(review),
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


def migrate_journal(source: Path, target: Path) -> list[str]:
    """Convert *source* v1 journal into a new v2 journal at *target*."""

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
    tasks, reviews = _load_source(source)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.migration-", dir=target.parent))
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
