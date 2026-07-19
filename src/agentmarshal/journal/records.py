"""Append-only journal evidence records."""

from __future__ import annotations

import json
import secrets
import threading
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_RANDOM_MASK = (1 << 80) - 1
_ulid_lock = threading.Lock()
_last_timestamp = -1
_last_randomness = 0


class JournalRecordError(ValueError):
    """Raised when a journal record is malformed."""


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


def _validate_record(record: Mapping[str, object]) -> dict[str, object]:
    data = dict(record)
    if type(data.get("schema")) is not int or data["schema"] != 1:
        raise JournalRecordError("record has an unknown or missing schema version")
    for field in ("record_type", "task", "created_at"):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            raise JournalRecordError(f"record field {field!r} must be a non-empty string")
    try:
        created_at = datetime.fromisoformat(cast(str, data["created_at"]).replace("Z", "+00:00"))
    except ValueError as error:
        raise JournalRecordError("record field 'created_at' must be an ISO-8601 timestamp") from error
    if created_at.tzinfo is None or created_at.utcoffset() != UTC.utcoffset(created_at):
        raise JournalRecordError("record field 'created_at' must be a UTC timestamp")
    if data["record_type"] == "opened":
        tool_version = data.get("tool_version")
        if not isinstance(tool_version, str) or not tool_version:
            raise JournalRecordError("opened record field 'tool_version' must be a non-empty string")
    return data


def _record_path(journal_root: Path, task_id: str, record_id: str, record_type: str) -> Path:
    if not task_id or Path(task_id).name != task_id:
        raise JournalRecordError("task id must be a single path component")
    if not record_type or Path(record_type).name != record_type:
        raise JournalRecordError("record type must be a single path component")
    return journal_root / "tasks" / task_id / "records" / f"{record_id}-{record_type}.json"


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
    if len(identifier) != 26 or any(char not in _CROCKFORD_BASE32 for char in identifier):
        raise JournalRecordError("record id must be a 26-character Crockford base32 ULID")
    path = _record_path(journal_root, task_id, identifier, record_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    with path.open("x", encoding="utf-8", newline="\n") as record_file:
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


def read_records(journal_root: Path, task_id: str) -> list[dict[str, object]]:
    """Load and validate all evidence records for one task in path order."""

    records_directory = journal_root / "tasks" / task_id / "records"
    if not records_directory.exists():
        return []
    if not records_directory.is_dir():
        raise JournalRecordError(f"record directory is not a directory: {records_directory}")
    records: list[dict[str, object]] = []
    for path in sorted(records_directory.glob("*.json")):
        with path.open("r", encoding="utf-8-sig") as record_file:
            try:
                loaded = json.load(record_file)
            except json.JSONDecodeError as error:
                raise JournalRecordError(f"invalid JSON record: {path}") from error
        if not isinstance(loaded, dict):
            raise JournalRecordError(f"record must contain a JSON object: {path}")
        record = _validate_record(cast(dict[str, object], loaded))
        if record["task"] != task_id:
            raise JournalRecordError(f"record task does not match its directory: {path}")
        records.append(record)
    return records
