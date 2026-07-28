"""Backfill: import retained v1 stat records as imported session records.

The journal-revision audit found token economics were never durable — they
live only in gitignored v1 stat records. ADR-0005 Decision 4 sanctions a
retroactive backfill that imports that retained host data into the journal
as *provenance-marked* records: every imported record is
``imported-from-host``, never ``live``, because it was not attested at the
moment of the event.

This module is the pure mapping layer: it turns a v1 stat record into a
schema-2 ``session`` record, preserving the original timestamp, and
validates it. It writes nothing to the journal — the restore run that
commits the records through the measurements lane (CR-028) is a separate
data operation that consumes this library.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

from agentmarshal import __version__
from agentmarshal.journal.attestation import SOURCE_IMPORTED
from agentmarshal.journal.capture import CaptureError, assert_no_leaks
from agentmarshal.journal.records import (
    JournalRecordError,
    validate_record_content,
    validate_task_id,
)

# A synthetic session filename to drive record validation through the
# public record validator (name + content), which also checks the record
# type matches. The id is a placeholder; the real id is assigned when the
# restore run writes the record.
_VALIDATION_FILENAME = "01J00000000000000000000000-session.json"

# The session record's activity vocabulary (records.py). A stat activity
# outside it is normalized to "other" rather than rejected — the point of
# the backfill is to preserve economics, not to relitigate taxonomy.
_SESSION_ACTIVITIES = frozenset({"implementation", "review", "other"})

# v1 stat fields the mapping reads. A record missing one is malformed and
# fails closed.
_REQUIRED_STAT_FIELDS = (
    "task",
    "recorded_at",
    "role",
    "vendor",
    "model",
    "activity",
    "outcome",
    "input_tokens",
    "output_tokens",
)


class BackfillError(ValueError):
    """Raised when a stat record cannot be imported."""


def _require_int(stat: dict[str, object], field: str) -> int:
    value = stat.get(field, 0)
    if type(value) is not int or value < 0:
        raise BackfillError(f"stat field {field!r} must be a non-negative integer")
    return value


def source_hash(raw: bytes) -> str:
    """Return the SHA-256 hex digest of a source file's exact bytes."""

    return hashlib.sha256(raw).hexdigest()


def session_record_from_stat(
    stat: dict[str, object],
    *,
    source_ref: str,
    source_digest: str,
    imported_at: str,
) -> dict[str, object]:
    """Map a v1 stat record to a validated schema-2 imported session record.

    ``created_at`` is the stat's original ``recorded_at`` (not now), and
    ``source`` is always ``imported-from-host``. The cache token count sums
    cache-read and cache-creation so no token is dropped.

    Provenance (ADR-0005 Decision 4) is pinned in an ``artifacts`` entry:
    its ``hash`` is the SHA-256 of the source file's exact bytes (so a
    modified or substituted source is detectable) and its ``ref`` carries
    the source identity and the import time (so a duplicate is detectable
    and the import is dated). The record is validated and leak-scanned
    before it is returned; a malformed mapping raises.
    """

    if not source_ref:
        raise BackfillError("source_ref must be a non-empty string")
    if not imported_at:
        raise BackfillError("imported_at must be a non-empty timestamp")

    for field in _REQUIRED_STAT_FIELDS:
        if field not in stat:
            raise BackfillError(f"stat record is missing required field {field!r}")

    for field in ("task", "recorded_at", "role", "vendor", "model", "activity"):
        value = stat[field]
        if not isinstance(value, str) or not value:
            raise BackfillError(f"stat field {field!r} must be a non-empty string")

    try:
        validate_task_id(str(stat["task"]))
    except JournalRecordError as error:
        raise BackfillError(f"stat has an invalid task id: {error}") from error

    outcome = stat["outcome"]
    if not isinstance(outcome, str) or not outcome:
        raise BackfillError("stat field 'outcome' must be a non-empty string")

    activity = stat["activity"]
    normalized_activity = activity if activity in _SESSION_ACTIVITIES else "other"

    cache_tokens = _require_int(stat, "cache_read_input_tokens") + _require_int(
        stat, "cache_creation_input_tokens"
    )

    record: dict[str, object] = {
        "schema": 2,
        "record_type": "session",
        "task": stat["task"],
        "created_at": stat["recorded_at"],
        "tool_version": __version__,
        "role": stat["role"],
        "actor": f"{stat['vendor']}/{stat['model']}",
        "activity": normalized_activity,
        "outcome": outcome,
        "tokens": {
            "input": _require_int(stat, "input_tokens"),
            "output": _require_int(stat, "output_tokens"),
            "cache": cache_tokens,
        },
        "source": SOURCE_IMPORTED,
        "artifacts": [
            {
                "ref": f"host-stat:{source_ref};imported-at={imported_at}",
                "hash": source_digest,
            }
        ],
    }

    serialized = json.dumps(record, ensure_ascii=False)
    try:
        validate_record_content(_VALIDATION_FILENAME, serialized)
    except JournalRecordError as error:
        raise BackfillError(f"mapped session record is invalid: {error}") from error

    # Mandatory leak-scan before an importable record leaves the mapper
    # (ADR-0005): a stat that smuggled a secret into a free-text field is
    # refused rather than restored.
    try:
        assert_no_leaks(serialized)
    except CaptureError as error:
        raise BackfillError(f"stat record trips the leak scan: {error}") from error

    # Honesty invariant (ADR-0005 Decision 4): backfilled evidence is never
    # presented as live.
    assert record["source"] == SOURCE_IMPORTED
    return record


def _read_stat_files(
    stats_dir: Path,
) -> Iterator[tuple[str, bytes, dict[str, object]]]:
    """Yield (stat_id, raw_bytes, stat) for every stat JSON in *stats_dir*.

    The exact bytes are retained so provenance can hash the source file
    before JSON decoding. Unrelated files (anything not a ``RUN-*.json``)
    are ignored, so the directory can hold other host state.
    """

    if not stats_dir.is_dir():
        raise BackfillError(f"{stats_dir}: stats directory is not a directory")
    for path in sorted(stats_dir.iterdir()):
        if (
            not path.is_file()
            or path.suffix != ".json"
            or not path.name.startswith("RUN-")
        ):
            continue
        try:
            raw = path.read_bytes()
            loaded = json.loads(raw.decode("utf-8-sig"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BackfillError(f"{path}: cannot read stat record: {error}") from error
        if not isinstance(loaded, dict):
            raise BackfillError(f"{path}: stat record must be a JSON object")
        yield path.stem, raw, loaded


def _map_file(
    stat_id: str, raw: bytes, stat: dict[str, object], imported_at: str
) -> dict[str, object]:
    return session_record_from_stat(
        stat,
        source_ref=stat_id,
        source_digest=source_hash(raw),
        imported_at=imported_at,
    )


def backfill_sessions(stats_dir: Path, imported_at: str) -> list[dict[str, object]]:
    """Map every stat record in *stats_dir* to an imported session record."""

    return [
        _map_file(stat_id, raw, stat, imported_at)
        for stat_id, raw, stat in _read_stat_files(stats_dir)
    ]


def backfill_task_sessions(
    stats_dir: Path, task_id: str, imported_at: str
) -> list[dict[str, object]]:
    """Return the imported session records for *task_id*, deterministically ordered.

    Ordered by the original timestamp then the stat id, so the restore
    writes a stable sequence.
    """

    validate_task_id(task_id)
    selected: list[tuple[str, str, dict[str, object]]] = []
    for stat_id, raw, stat in _read_stat_files(stats_dir):
        if stat.get("task") != task_id:
            continue
        record = _map_file(stat_id, raw, stat, imported_at)
        selected.append((str(record["created_at"]), stat_id, record))
    selected.sort(key=lambda item: (item[0], item[1]))
    return [record for _, _, record in selected]
