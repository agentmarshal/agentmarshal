"""Append-only journal evidence records."""

from __future__ import annotations

import json
import re
import secrets
import threading
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

# Reuse the hardened no-follow exclusive creator from project.py so record
# files get the same symlink/race guarantees as the project file.
from agentmarshal.project import UnsafeProjectPathError, _create_exclusive

_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_RANDOM_MASK = (1 << 80) - 1
_TASK_ID_PATTERN = re.compile(r"CR-[0-9]+$")
_RECORD_FILENAME_PATTERN = re.compile(
    r"(?P<record_id>[0-7][0123456789ABCDEFGHJKMNPQRSTVWXYZ]{25})-"
    r"(?P<record_type>[a-z]+)\.json$"
)
_RECORD_FIELDS = {
    "opened": frozenset(
        {"schema", "record_type", "task", "created_at", "tool_version"}
    ),
    "review": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "reviewed_commit",
            "verdict",
            "reviewer",
            "findings",
        }
    ),
    "completed": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "completed_commit",
        }
    ),
    "abandoned": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "reason",
        }
    ),
    "session": frozenset(
        {
            "schema",
            "record_type",
            "task",
            "created_at",
            "tool_version",
            "role",
            "actor",
            "activity",
            "outcome",
            "tokens",
        }
    ),
}
_REVIEWED_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}$")
_REVIEW_VERDICTS = frozenset({"approved", "changes_required", "blocked", "rejected"})
_SESSION_ACTIVITIES = frozenset({"implementation", "review", "other"})
_ulid_lock = threading.Lock()
_last_timestamp = -1
_last_randomness = 0


class JournalRecordError(ValueError):
    """Raised when a journal record is malformed."""


def validate_task_id(task_id: str) -> None:
    """Raise when *task_id* is not a canonical journal task identifier."""

    if _TASK_ID_PATTERN.fullmatch(task_id) is None:
        raise JournalRecordError("task id must match CR-<number>")


def _encode_base32(value: int, length: int) -> str:
    characters = ["0"] * length
    for index in range(length - 1, -1, -1):
        characters[index] = _CROCKFORD_BASE32[value & 31]
        value >>= 5
    return "".join(characters)


def generate_ulid() -> str:
    """Return a lexicographically sortable ULID-class identifier."""

    global _last_randomness, _last_timestamp
    timestamp = time.time_ns() // 1_000_000
    with _ulid_lock:
        if timestamp > _last_timestamp:
            randomness = secrets.randbits(80)
        else:
            timestamp = _last_timestamp
            randomness = _last_randomness + 1
            if randomness > _ULID_RANDOM_MASK:
                timestamp += 1
                randomness = secrets.randbits(80)
        _last_timestamp = timestamp
        _last_randomness = randomness
    return _encode_base32(timestamp, 10) + _encode_base32(randomness, 16)


def _is_ulid(value: str) -> bool:
    return (
        len(value) == 26
        and value[0] in "01234567"
        and all(character in _CROCKFORD_BASE32 for character in value)
    )


def _validate_record(record: Mapping[str, object]) -> dict[str, object]:
    data = dict(record)
    if type(data.get("schema")) is not int or data["schema"] != 1:
        raise JournalRecordError("record has an unknown or missing schema version")
    record_type = data.get("record_type")
    if not isinstance(record_type, str) or record_type not in _RECORD_FIELDS:
        raise JournalRecordError("record has an unknown or missing record type")
    unexpected_fields = data.keys() - _RECORD_FIELDS[record_type]
    if unexpected_fields:
        raise JournalRecordError(
            f"record has unsupported fields: {', '.join(sorted(unexpected_fields))}"
        )
    for field in ("record_type", "task", "created_at"):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(
                f"record field {field!r} must be a non-empty string"
            )
    try:
        created_at = datetime.fromisoformat(
            cast(str, data["created_at"]).replace("Z", "+00:00")
        )
    except ValueError as error:
        raise JournalRecordError(
            "record field 'created_at' must be an ISO-8601 timestamp"
        ) from error
    if created_at.tzinfo is None or created_at.utcoffset() != UTC.utcoffset(created_at):
        raise JournalRecordError("record field 'created_at' must be a UTC timestamp")
    tool_version = data.get("tool_version")
    if not isinstance(tool_version, str) or not tool_version:
        raise JournalRecordError(
            "record field 'tool_version' must be a non-empty string"
        )
    if record_type == "review":
        _validate_review_record(data)
    elif record_type == "completed":
        completed_commit = data.get("completed_commit")
        if (
            not isinstance(completed_commit, str)
            or _REVIEWED_COMMIT_PATTERN.fullmatch(completed_commit) is None
        ):
            raise JournalRecordError(
                "completed record field 'completed_commit' must be exactly 40 "
                "lowercase hex characters"
            )
    elif record_type == "abandoned":
        reason = data.get("reason")
        if not isinstance(reason, str) or not reason:
            raise JournalRecordError(
                "abandoned record field 'reason' must be a non-empty string"
            )
    elif record_type == "session":
        _validate_session_record(data)
    return data


def _validate_review_record(data: Mapping[str, object]) -> None:
    reviewed_commit = data.get("reviewed_commit")
    if (
        not isinstance(reviewed_commit, str)
        or _REVIEWED_COMMIT_PATTERN.fullmatch(reviewed_commit) is None
    ):
        raise JournalRecordError(
            "review record field 'reviewed_commit' must be exactly 40 lowercase hex characters"
        )
    verdict = data.get("verdict")
    if not isinstance(verdict, str) or verdict not in _REVIEW_VERDICTS:
        raise JournalRecordError(
            "review record field 'verdict' must be one of approved, changes_required, "
            "blocked, or rejected"
        )
    reviewer = data.get("reviewer")
    if not isinstance(reviewer, dict):
        raise JournalRecordError("review record field 'reviewer' must be an object")
    for field in ("role", "vendor", "model", "email"):
        value = reviewer.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(
                f"review record reviewer field {field!r} must be a non-empty string"
            )
    email = reviewer["email"]
    if not isinstance(email, str) or "@" not in email:
        raise JournalRecordError(
            "review record reviewer field 'email' must contain '@'"
        )
    if reviewer.keys() != {"role", "vendor", "model", "email"}:
        raise JournalRecordError(
            "review record field 'reviewer' must contain only role, vendor, "
            "model, and email"
        )
    findings = data.get("findings")
    if not isinstance(findings, list) or not all(
        isinstance(finding, str) and finding for finding in findings
    ):
        raise JournalRecordError(
            "review record field 'findings' must be an array of non-empty finding ids"
        )
    if len(set(findings)) != len(findings):
        raise JournalRecordError("review record findings must have unique finding ids")
    if verdict == "approved" and findings:
        raise JournalRecordError("approved review records must have no findings")
    if verdict != "approved" and not findings:
        raise JournalRecordError(
            "non-approved review records must have at least one finding id"
        )


def _validate_session_record(data: Mapping[str, object]) -> None:
    for field in ("role", "actor", "outcome"):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(
                f"session record field {field!r} must be a non-empty string"
            )
    activity = data.get("activity")
    if not isinstance(activity, str) or activity not in _SESSION_ACTIVITIES:
        raise JournalRecordError(
            "session record field 'activity' must be one of implementation, review, "
            "or other"
        )
    tokens = data.get("tokens")
    if not isinstance(tokens, dict) or tokens.keys() != {"input", "output", "cache"}:
        raise JournalRecordError(
            "session record field 'tokens' must contain only input, output, and cache"
        )
    for field in ("input", "output", "cache"):
        value = tokens[field]
        if type(value) is not int or value < 0:
            raise JournalRecordError(
                f"session record token {field!r} must be an integer greater than or equal to zero"
            )


def _record_path(
    journal_root: Path, task_id: str, record_id: str, record_type: str
) -> Path:
    validate_task_id(task_id)
    if not record_type or Path(record_type).name != record_type:
        raise JournalRecordError("record type must be a single path component")
    return (
        journal_root / "tasks" / task_id / "records" / f"{record_id}-{record_type}.json"
    )


def ensure_journal_root_is_real(journal_root: Path) -> None:
    """Reject a journal root reachable through a symlinked ancestor.

    ``journal_root`` must be built from a resolved project root; a resolve
    mismatch means some ancestor (for example the project metadata
    directory itself) is a symlink and evidence I/O would escape the
    repository.
    """

    resolved_root = journal_root.resolve()
    if resolved_root != journal_root:
        raise JournalRecordError(
            "journal root resolves outside its expected location: "
            f"{journal_root} -> {resolved_root}"
        )


def _prepare_record_directory(journal_root: Path, task_id: str) -> Path:
    ensure_journal_root_is_real(journal_root)
    paths = (journal_root, journal_root / "tasks", journal_root / "tasks" / task_id)
    for path in paths:
        if path.is_symlink():
            raise JournalRecordError(f"refusing to write through a symlink: {path}")
        if path.exists() and not path.is_dir():
            raise JournalRecordError(f"record path is not a directory: {path}")
        path.mkdir(exist_ok=True)
    records_directory = paths[-1] / "records"
    if records_directory.is_symlink():
        raise JournalRecordError(
            f"refusing to write through a symlink: {records_directory}"
        )
    if records_directory.exists() and not records_directory.is_dir():
        raise JournalRecordError(f"record path is not a directory: {records_directory}")
    records_directory.mkdir(exist_ok=True)
    resolved_directory = records_directory.resolve()
    if resolved_directory != records_directory:
        raise JournalRecordError(
            "record directory resolves outside its expected location: "
            f"{records_directory} -> {resolved_directory}"
        )
    return records_directory


def write_record(
    journal_root: Path,
    task_id: str,
    record: Mapping[str, object],
    *,
    record_id: str | None = None,
) -> Path:
    """Exclusively create an evidence record and return its path."""

    data = _validate_record(record)
    if data["task"] != task_id:
        raise JournalRecordError("record task does not match its destination")
    record_type = cast(str, data["record_type"])
    identifier = generate_ulid() if record_id is None else record_id
    if not _is_ulid(identifier):
        raise JournalRecordError(
            "record id must be a 26-character Crockford base32 ULID"
        )
    path = _record_path(journal_root, task_id, identifier, record_type)
    _prepare_record_directory(journal_root, task_id)
    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    try:
        record_file = _create_exclusive(path)
    except UnsafeProjectPathError as error:
        raise JournalRecordError(str(error)) from error
    with record_file:
        record_file.write(f"{content}\n")
    return path


def create_opened_record(task_id: str, tool_version: str) -> dict[str, object]:
    """Build the lifecycle record emitted when a task is opened."""

    return {
        "schema": 1,
        "record_type": "opened",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
    }


def create_completed_record(
    task_id: str, tool_version: str, completed_commit: str
) -> dict[str, object]:
    """Build the terminal record emitted when a task is completed."""

    return {
        "schema": 1,
        "record_type": "completed",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "completed_commit": completed_commit,
    }


def create_abandoned_record(
    task_id: str, tool_version: str, reason: str
) -> dict[str, object]:
    """Build the terminal record emitted when a task is abandoned."""

    return {
        "schema": 1,
        "record_type": "abandoned",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "reason": reason,
    }


def create_session_record(
    task_id: str,
    tool_version: str,
    role: str,
    actor: str,
    activity: str,
    outcome: str,
    input_tokens: int,
    output_tokens: int,
    cache_tokens: int,
) -> dict[str, object]:
    """Build an attributed work session record."""

    return {
        "schema": 1,
        "record_type": "session",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "role": role,
        "actor": actor,
        "activity": activity,
        "outcome": outcome,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "cache": cache_tokens,
        },
    }


def create_review_record(
    task_id: str,
    tool_version: str,
    reviewed_commit: str,
    verdict: str,
    reviewer_role: str,
    reviewer_vendor: str,
    reviewer_model: str,
    reviewer_email: str,
    findings: list[str],
) -> dict[str, object]:
    """Build the review evidence record submitted by a reviewer."""

    return {
        "schema": 1,
        "record_type": "review",
        "task": task_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tool_version": tool_version,
        "reviewed_commit": reviewed_commit,
        "verdict": verdict,
        "reviewer": {
            "role": reviewer_role,
            "vendor": reviewer_vendor,
            "model": reviewer_model,
            "email": reviewer_email,
        },
        "findings": findings,
    }


def validate_record_content(filename: str, content: str) -> dict[str, object]:
    """Validate a record file's name and JSON content; return the record."""

    match = _RECORD_FILENAME_PATTERN.fullmatch(filename)
    if match is None:
        raise JournalRecordError(f"record filename is malformed: {filename}")
    try:
        loaded = json.loads(content)
    except json.JSONDecodeError as error:
        raise JournalRecordError(f"invalid JSON record: {filename}") from error
    if not isinstance(loaded, dict):
        raise JournalRecordError(f"record must contain a JSON object: {filename}")
    record = _validate_record(cast(dict[str, object], loaded))
    if record["record_type"] != match["record_type"]:
        raise JournalRecordError(f"record type does not match its filename: {filename}")
    return record


def read_records(journal_root: Path, task_id: str) -> list[dict[str, object]]:
    """Load and validate all evidence records for one task in path order."""

    validate_task_id(task_id)
    ensure_journal_root_is_real(journal_root)
    if journal_root.is_symlink():
        raise JournalRecordError(f"refusing to read through a symlink: {journal_root}")
    tasks_directory = journal_root / "tasks"
    task_directory = tasks_directory / task_id
    for path in (tasks_directory, task_directory):
        if path.is_symlink():
            raise JournalRecordError(f"refusing to read through a symlink: {path}")
    records_directory = journal_root / "tasks" / task_id / "records"
    if records_directory.is_symlink():
        raise JournalRecordError(
            f"refusing to read through a symlink: {records_directory}"
        )
    if not records_directory.exists():
        return []
    if not records_directory.is_dir():
        raise JournalRecordError(
            f"record directory is not a directory: {records_directory}"
        )
    records: list[dict[str, object]] = []
    for path in sorted(records_directory.iterdir()):
        if path.is_symlink():
            raise JournalRecordError(f"refusing to read through a symlink: {path}")
        if not path.is_file():
            raise JournalRecordError(f"record path is not a file: {path}")
        filename = _RECORD_FILENAME_PATTERN.fullmatch(path.name)
        if filename is None:
            raise JournalRecordError(f"record filename is malformed: {path}")
        with path.open("r", encoding="utf-8-sig") as record_file:
            try:
                loaded = json.load(record_file)
            except json.JSONDecodeError as error:
                raise JournalRecordError(f"invalid JSON record: {path}") from error
        if not isinstance(loaded, dict):
            raise JournalRecordError(f"record must contain a JSON object: {path}")
        try:
            record = _validate_record(cast(dict[str, object], loaded))
        except JournalRecordError as error:
            raise JournalRecordError(f"{error}: {path}") from error
        if record["task"] != task_id:
            raise JournalRecordError(
                f"record task does not match its directory: {path}"
            )
        if record["record_type"] != filename["record_type"]:
            raise JournalRecordError(f"record type does not match its filename: {path}")
        record["id"] = filename["record_id"]
        records.append(record)
    return records
