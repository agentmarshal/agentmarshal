"""Tests for session activity records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.journal.records import (
    JournalRecordError,
    create_session_record,
    generate_ulid,
    read_records,
    write_record,
)


def _session_record(activity: str) -> dict[str, object]:
    return create_session_record(
        "CR-001", "test", "lead", "agent", activity, "done", 1, 2, 3
    )


def test_coordinating_session_is_recorded_as_such(tmp_path: Path) -> None:
    """Scenario: a coordinating session is recorded as such."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_record("coordination"))

    records = read_records(journal_root, "CR-001")
    assert records[0]["activity"] == "coordination"


def test_activity_outside_the_vocabulary_is_still_refused(
    tmp_path: Path,
) -> None:
    """Scenario: an activity outside the vocabulary is still refused."""

    journal_root = tmp_path / "journal"

    with pytest.raises(JournalRecordError, match="activity"):
        write_record(journal_root, "CR-001", _session_record("planning"))

    assert not journal_root.exists()


def test_coordination_stamps_the_newer_schema(tmp_path: Path) -> None:
    """Scenario: coordination stamps the newer schema."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_record("coordination"))

    assert read_records(journal_root, "CR-001")[0]["schema"] == 6

    older_schema = _session_record("coordination")
    older_schema["schema"] = 3
    with pytest.raises(JournalRecordError, match="requires schema 6"):
        write_record(tmp_path / "older-journal", "CR-001", older_schema)


@pytest.mark.parametrize("activity", ("implementation", "review", "other"))
def test_other_activities_keep_their_schema(activity: str, tmp_path: Path) -> None:
    """Scenario: other activities keep their schema."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_record(activity))

    assert read_records(journal_root, "CR-001")[0]["schema"] == 3


# --- the session fields of schema 7 (ADR-0022 section 2) -------------------

_COMMIT = "a" * 40
_FAMILY_VALUES: dict[str, object] = {
    "commit": _COMMIT,
    "model": "swe-2",
    "trace": "https://trace.example/run-1",
    "cli_session": "cli-123",
    "report_ready": True,
    "fallback_reason": "provider limit",
}
_STRING_FIELDS = ("commit", "model", "trace", "cli_session", "fallback_reason")


def _session_with(**fields: Any) -> dict[str, object]:
    return create_session_record(
        "CR-001",
        "test",
        "implementer",
        "agent",
        "implementation",
        "done",
        1,
        2,
        3,
        **fields,
    )


def test_a_session_carrying_the_new_fields_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a session carrying the new fields is written and read back."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_with(**_FAMILY_VALUES))

    stored = read_records(journal_root, "CR-001")[0]
    for field, value in _FAMILY_VALUES.items():
        assert stored[field] == value


def test_each_new_field_is_optional(tmp_path: Path) -> None:
    """Scenario: each new field is optional."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_record("implementation"))

    stored = read_records(journal_root, "CR-001")[0]
    for field in _FAMILY_VALUES:
        assert field not in stored


@pytest.mark.parametrize(
    "commit", ["a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + " ", 40]
)
def test_a_commit_that_is_not_40_lowercase_hex_is_refused(
    commit: object, tmp_path: Path
) -> None:
    """Scenario: a commit that is not 40 lowercase hex is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"40 .*lowercase hex"):
        write_record(journal_root, "CR-001", _session_with(commit=commit))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", ("model", "trace", "cli_session", "fallback_reason"))
@pytest.mark.parametrize("value", ["", "   ", 5])
def test_an_empty_string_field_is_refused(
    field: str, value: object, tmp_path: Path
) -> None:
    """Scenario: an empty string field is refused.

    All-whitespace is refused with the empty string: it carries nothing a
    reader could use, so the check measures non-empty after a strip, as
    the `reopened`, `amendment` and `acceptance` reasons already do.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="non-empty string"):
        write_record(journal_root, "CR-001", _session_with(**{field: value}))

    assert not journal_root.exists()


@pytest.mark.parametrize("value", ["yes", 1, 0])
def test_a_report_ready_that_is_not_a_boolean_is_refused(
    value: object, tmp_path: Path
) -> None:
    """Scenario: a report_ready that is not a boolean is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="must be a boolean"):
        write_record(journal_root, "CR-001", _session_with(report_ready=value))

    assert not journal_root.exists()


def test_report_ready_false_is_written_and_read_back(tmp_path: Path) -> None:
    """`report_ready: false` is a value carried, not a field omitted.

    `create_session_record` sets each family field on `is not None`, so a
    false report_ready is written — and its presence is a family field, so
    the record stamps 7. A truthiness test would silently drop it.
    """

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_with(report_ready=False))

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["report_ready"] is False
    assert stored["schema"] == 7


@pytest.mark.parametrize("field", _STRING_FIELDS)
def test_a_string_field_that_could_forge_a_rendered_line_is_refused(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a string field that could forge a rendered line is refused.

    `model`, `trace`, `cli_session` and `fallback_reason` meet the
    forgeable-text refusal; `commit` meets its own 40-hex shape refusal
    first, which admits no forgeable character — the registration would
    never fire, so the family registers the four displayed strings only.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"control characters|lowercase hex"):
        write_record(journal_root, "CR-001", _session_with(**{field: "ok\nforged"}))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", tuple(_FAMILY_VALUES))
def test_a_session_carrying_a_field_of_the_family_stamps_schema_7(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a session carrying a field of the family stamps schema 7."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root, "CR-001", _session_with(**{field: _FAMILY_VALUES[field]})
    )

    assert read_records(journal_root, "CR-001")[0]["schema"] == 7


@pytest.mark.parametrize("field", tuple(_FAMILY_VALUES))
def test_a_field_of_the_family_on_a_session_below_schema_7_is_refused_at_write(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a field of the family on a session below schema 7 is
    refused at write."""

    journal_root = tmp_path / "journal"
    record = _session_with(**{field: _FAMILY_VALUES[field]})
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("field", tuple(_FAMILY_VALUES))
def test_a_field_of_the_family_on_a_session_below_schema_7_is_refused_on_read(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a field of the family on a session below schema 7 is
    refused on read."""

    record = _session_with(**{field: _FAMILY_VALUES[field]})
    record["schema"] = 6
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-session.json").write_text(
        json.dumps(record), encoding="utf-8"
    )

    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(tmp_path / "journal", "CR-001")


@pytest.mark.parametrize(
    "activity,expected",
    [("implementation", 3), ("review", 3), ("other", 3), ("coordination", 6)],
)
def test_a_session_without_the_family_keeps_its_schema(
    activity: str, expected: int, tmp_path: Path
) -> None:
    """Scenario: a session without the family keeps its schema."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_record(activity))

    assert read_records(journal_root, "CR-001")[0]["schema"] == expected


@pytest.mark.parametrize("activity", ("implementation", "review", "other"))
def test_a_non_coordination_session_carrying_a_schema_7_field_carries_7(
    activity: str, tmp_path: Path
) -> None:
    """Scenario: a non-coordination session carrying a schema-7 field
    carries 7."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root,
        "CR-001",
        create_session_record(
            "CR-001",
            "test",
            "implementer",
            "agent",
            activity,
            "done",
            1,
            2,
            3,
            model="m",
        ),
    )

    assert read_records(journal_root, "CR-001")[0]["schema"] == 7
