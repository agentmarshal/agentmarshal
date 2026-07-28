"""Tests for the in-toto attestation vocabulary and schema-2 records."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.journal.attestation import (
    PREDICATE_TYPES,
    SOURCE_IMPORTED,
    SOURCE_LIVE,
    UnknownPredicateTypeError,
    is_registered_record_type,
    predicate_type_for,
)
from agentmarshal.journal.records import (
    _RECORD_FIELDS,
    JournalRecordError,
    read_records,
    write_record,
)

_HEX64 = "a" * 64


def _opened_v2(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": 2,
        "record_type": "opened",
        "task": "CR-001",
        "created_at": "2026-07-19T00:00:00Z",
        "tool_version": "1.0",
        "source": SOURCE_LIVE,
    }
    record.update(overrides)
    return record


# --- registry -------------------------------------------------------------


def test_predicate_type_for_returns_registered_uri() -> None:
    assert predicate_type_for("review") == PREDICATE_TYPES["review"]
    assert predicate_type_for("completed").startswith("https://agentmarshal.dev/")


def test_predicate_type_for_unregistered_fails_closed() -> None:
    with pytest.raises(UnknownPredicateTypeError):
        predicate_type_for("nope")
    assert not is_registered_record_type("nope")


def test_every_accepted_record_type_is_registered() -> None:
    # The completeness check depends on this coupling: a record type the
    # validator accepts must be projectable to an in-toto Statement.
    assert set(_RECORD_FIELDS) == set(PREDICATE_TYPES)


# --- schema-2 acceptance --------------------------------------------------


def test_schema_2_round_trip_with_source_and_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    record = _opened_v2(
        source=SOURCE_IMPORTED,
        artifacts=[{"ref": "runs/CR-001-prompt.md", "hash": _HEX64}],
    )
    identifier = "01J00000000000000000000000"
    write_record(root, "CR-001", record, record_id=identifier)
    assert read_records(root, "CR-001") == [record | {"id": identifier}]


def test_schema_2_without_artifacts_is_valid(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    write_record(root, "CR-001", _opened_v2(), record_id="01J00000000000000000000001")
    stored = read_records(root, "CR-001")
    assert stored[0]["source"] == SOURCE_LIVE
    assert "artifacts" not in stored[0]


# --- schema-2 rejections --------------------------------------------------


def test_schema_2_without_source_is_rejected(tmp_path: Path) -> None:
    record = _opened_v2()
    del record["source"]
    with pytest.raises(JournalRecordError, match="source"):
        write_record(tmp_path / "journal", "CR-001", record)


def test_schema_2_bad_source_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(JournalRecordError, match="source"):
        write_record(tmp_path / "journal", "CR-001", _opened_v2(source="fabricated"))


@pytest.mark.parametrize(
    "artifacts",
    [
        "not-a-list",
        [{"ref": "x", "hash": _HEX64, "extra": 1}],
        [{"ref": "x"}],
        [{"ref": "", "hash": _HEX64}],
        [{"ref": "x", "hash": "a" * 63}],
        [{"ref": "x", "hash": "A" * 64}],
    ],
)
def test_schema_2_malformed_artifacts_are_rejected(
    tmp_path: Path, artifacts: object
) -> None:
    with pytest.raises(JournalRecordError):
        write_record(tmp_path / "journal", "CR-001", _opened_v2(artifacts=artifacts))


# --- schema-1 stays strict ------------------------------------------------


def test_schema_1_carrying_source_is_rejected(tmp_path: Path) -> None:
    record = {
        "schema": 1,
        "record_type": "opened",
        "task": "CR-001",
        "created_at": "2026-07-19T00:00:00Z",
        "tool_version": "1.0",
        "source": SOURCE_LIVE,
    }
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(tmp_path / "journal", "CR-001", record)


def test_schema_1_carrying_artifacts_is_rejected(tmp_path: Path) -> None:
    record = {
        "schema": 1,
        "record_type": "opened",
        "task": "CR-001",
        "created_at": "2026-07-19T00:00:00Z",
        "tool_version": "1.0",
        "artifacts": [{"ref": "x", "hash": _HEX64}],
    }
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(tmp_path / "journal", "CR-001", record)


def test_unknown_schema_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(JournalRecordError, match="schema"):
        write_record(tmp_path / "journal", "CR-001", _opened_v2(schema=3))
