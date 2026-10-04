"""Tests for session activity records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
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
_FAMILY_VALUES: dict[str, Any] = {
    "commit": _COMMIT,
    "model": "swe-2",
    "trace": "https://trace.example/run-1",
    "cli_session": "cli-123",
    "report_ready": True,
    "fallback_reason": "provider limit",
}
_STRING_FIELDS = ("commit", "model", "trace", "cli_session", "fallback_reason")

# --- when a session ran, the reset time and the cost (ADR-0019, ADR-0022 s2)

_STARTED = "2026-10-01T10:00:00Z"
_ENDED = "2026-10-01T11:30:00Z"
_RESETS = "2026-10-02T00:00:00Z"
_COST: dict[str, str] = {"amount": "0.42", "currency": "USD", "source": "reported"}
# The kwargs that carry each field of the schema-7 session family:
# `started_at` and `ended_at` are admitted only together and `resets_at`
# only on a `provider-limit` outcome, so each name maps to a complete
# case for the stamps-7 and refused-below-7 parametrizations.
_FAMILY_STAMPS: dict[str, dict[str, Any]] = {
    **{field: {field: value} for field, value in _FAMILY_VALUES.items()},
    "started_at": {"started_at": _STARTED, "ended_at": _ENDED},
    "ended_at": {"started_at": _STARTED, "ended_at": _ENDED},
    "resets_at": {"outcome": "provider-limit", "resets_at": _RESETS},
    "cost": {"cost": dict(_COST)},
}


def _session_with(
    activity: str = "implementation", outcome: str = "done", **fields: Any
) -> dict[str, object]:
    return create_session_record(
        "CR-001",
        "test",
        "implementer",
        "agent",
        activity,
        outcome,
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
    for field in _FAMILY_STAMPS:
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
    field: str, value: Any, tmp_path: Path
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

    All five string fields register under the forgeable-text rule keyed
    `("session", field)`, `commit` included — its entry never fires, the
    40-hex shape rule refusing the forgeable character first, so `commit`
    meets that refusal and the other four meet the forgeable-text one.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"control characters|lowercase hex"):
        write_record(journal_root, "CR-001", _session_with(**{field: "ok\nforged"}))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", ("model", "trace", "cli_session", "fallback_reason"))
def test_no_length_bound_applies_to_the_family_fields(
    field: str, tmp_path: Path
) -> None:
    """ADR-0022 section 8 bounds no length for the family's fields.

    A value far past any bound the shared validators register is written
    and read back unchanged — the three length tables hold no entry for
    this family.
    """

    journal_root = tmp_path / "journal"
    long_value = "x" * 100_000
    write_record(journal_root, "CR-001", _session_with(**{field: long_value}))

    assert read_records(journal_root, "CR-001")[0][field] == long_value


@pytest.mark.parametrize("field", tuple(_FAMILY_STAMPS))
def test_a_session_carrying_a_field_of_the_family_stamps_schema_7(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a session carrying a field of the family stamps schema 7."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _session_with(**_FAMILY_STAMPS[field]))

    assert read_records(journal_root, "CR-001")[0]["schema"] == 7


@pytest.mark.parametrize("field", tuple(_FAMILY_STAMPS))
def test_a_field_of_the_family_on_a_session_below_schema_7_is_refused_at_write(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a field of the family on a session below schema 7 is
    refused at write."""

    journal_root = tmp_path / "journal"
    record = _session_with(**_FAMILY_STAMPS[field])
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("field", tuple(_FAMILY_STAMPS))
def test_a_field_of_the_family_on_a_session_below_schema_7_is_refused_on_read(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a field of the family on a session below schema 7 is
    refused on read."""

    record = _session_with(**_FAMILY_STAMPS[field])
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


@pytest.mark.parametrize("field", tuple(_FAMILY_STAMPS))
def test_a_coordination_session_carrying_a_schema_7_field_carries_7(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a coordination session carrying a schema-7 field
    carries 7."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root,
        "CR-001",
        _session_with("coordination", **_FAMILY_STAMPS[field]),
    )

    assert read_records(journal_root, "CR-001")[0]["schema"] == 7


def test_a_session_carrying_its_start_and_end_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a session carrying its start and end is written and read
    back."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root, "CR-001", _session_with(started_at=_STARTED, ended_at=_ENDED)
    )

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["started_at"] == _STARTED
    assert stored["ended_at"] == _ENDED
    assert stored["schema"] == 7


@pytest.mark.parametrize(
    "fields",
    [{"started_at": _STARTED}, {"ended_at": _ENDED}],
    ids=["a start without an end", "an end without a start"],
)
def test_a_start_without_an_end_or_an_end_without_a_start_is_refused(
    fields: dict[str, Any], tmp_path: Path
) -> None:
    """Scenario: a start without an end, or an end without a start, is
    refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="together or not at all"):
        write_record(journal_root, "CR-001", _session_with(**fields))

    assert not journal_root.exists()


def test_an_end_earlier_than_the_start_is_refused(tmp_path: Path) -> None:
    """Scenario: an end earlier than the start is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="earlier than 'started_at'"):
        write_record(
            journal_root,
            "CR-001",
            _session_with(started_at=_ENDED, ended_at=_STARTED),
        )

    assert not journal_root.exists()


def test_an_end_equal_to_the_start_is_admitted(tmp_path: Path) -> None:
    """Scenario: an end equal to the start is admitted."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root, "CR-001", _session_with(started_at=_STARTED, ended_at=_STARTED)
    )

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["ended_at"] == _STARTED


@pytest.mark.parametrize("field", ("started_at", "ended_at", "resets_at"))
@pytest.mark.parametrize(
    "value",
    [
        "not a time",
        "2026-10-01T10:00:00",
        "2026-10-01T10:00:00+02:00",
        5,
        None,
    ],
    ids=[
        "malformed",
        "no offset",
        "non-UTC offset",
        "not a string",
        "null",
    ],
)
def test_a_session_timestamp_that_is_not_a_utc_iso_8601_timestamp_is_refused(
    field: str, value: Any, tmp_path: Path
) -> None:
    """Scenario: a session timestamp that is not a UTC ISO-8601 timestamp is
    refused.

    The three timestamps follow `created_at`'s rule through the one
    parser: a naive timestamp and a non-UTC offset meet the UTC refusal,
    a malformed string, a non-string and an explicit `null` the ISO-8601
    one. Only the field under test is malformed — the pair is complete
    and the reset sits on a `provider-limit` outcome.
    """

    journal_root = tmp_path / "journal"
    record = _session_with(
        outcome="provider-limit",
        started_at=_STARTED,
        ended_at=_ENDED,
        resets_at=_RESETS,
    )
    # Assigned after the build — the builder drops a None argument, and
    # the test covers an explicit `null` carried in the record.
    record[field] = value
    with pytest.raises(JournalRecordError, match="timestamp"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_created_at_stays_the_write_time(tmp_path: Path) -> None:
    """Scenario: created_at stays the write time.

    `created_at` is stamped when the record is built — the write time —
    and derived from neither `started_at` nor `ended_at`.
    """

    before = datetime.now(UTC)
    record = _session_with(started_at=_STARTED, ended_at=_ENDED)
    after = datetime.now(UTC)

    created_at = datetime.fromisoformat(
        str(record["created_at"]).replace("Z", "+00:00")
    )
    assert before <= created_at <= after


def test_a_provider_limit_session_carrying_the_reset_time_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a provider-limit session carrying the reset time is written
    and read back."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root,
        "CR-001",
        _session_with(outcome="provider-limit", resets_at=_RESETS),
    )

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["resets_at"] == _RESETS
    assert stored["schema"] == 7


def test_resets_at_on_another_outcome_is_refused(tmp_path: Path) -> None:
    """Scenario: resets_at on another outcome is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="provider-limit"):
        write_record(journal_root, "CR-001", _session_with(resets_at=_RESETS))

    assert not journal_root.exists()


@pytest.mark.parametrize("amount", ("0", "12", "0.42"))
@pytest.mark.parametrize("cost_source", ("reported", "estimated"))
def test_a_session_carrying_a_cost_is_written_and_read_back(
    amount: str, cost_source: str, tmp_path: Path
) -> None:
    """Scenario: a session carrying a cost is written and read back."""

    journal_root = tmp_path / "journal"
    cost = {"amount": amount, "currency": "USD", "source": cost_source}
    write_record(journal_root, "CR-001", _session_with(cost=cost))

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["cost"] == cost
    assert stored["schema"] == 7


@pytest.mark.parametrize(
    "amount",
    [0, 1.5, -1, "+1", "1e3", ".5", "5.", " 1", "1 ", "", "-0.5"],
    ids=[
        "JSON integer",
        "JSON number",
        "negative number",
        "a sign",
        "an exponent",
        "a leading .",
        "a trailing .",
        "leading whitespace",
        "trailing whitespace",
        "empty",
        "negative string",
    ],
)
def test_an_amount_that_is_not_a_decimal_string_is_refused(
    amount: Any, tmp_path: Path
) -> None:
    """Scenario: an amount that is not a decimal string is refused.

    The JSON numbers 0 and 1.5 are refused with the string forms that are
    no decimal string — a sign, an exponent, a leading or trailing `.`,
    whitespace — so a sum over the amounts stays exact.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"cost.*amount"):
        write_record(
            journal_root,
            "CR-001",
            _session_with(
                cost={"amount": amount, "currency": "USD", "source": "reported"}
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "currency",
    ["usd", "US", "USDT", "", "US D", 5],
    ids=[
        "lowercase",
        "two letters",
        "four letters",
        "empty",
        "a space",
        "not a string",
    ],
)
def test_a_currency_that_is_not_three_uppercase_ascii_letters_is_refused(
    currency: Any, tmp_path: Path
) -> None:
    """Scenario: a currency that is not three uppercase ASCII letters is
    refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"cost.*currency"):
        write_record(
            journal_root,
            "CR-001",
            _session_with(
                cost={"amount": "1", "currency": currency, "source": "reported"}
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "cost_source",
    ["actual", "", "Reported", 5],
    ids=["outside the vocabulary", "empty", "wrong case", "not a string"],
)
def test_a_source_outside_the_vocabulary_is_refused(
    cost_source: Any, tmp_path: Path
) -> None:
    """Scenario: a source outside the vocabulary is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"cost.*source"):
        write_record(
            journal_root,
            "CR-001",
            _session_with(
                cost={"amount": "1", "currency": "USD", "source": cost_source}
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "cost",
    [
        "0.42",
        {"amount": "1", "currency": "USD"},
        {"amount": "1", "currency": "USD", "source": "reported", "fee": "0.1"},
        {},
        None,
    ],
    ids=[
        "not an object",
        "a missing key",
        "an extra key",
        "an empty object",
        "null",
    ],
)
def test_a_cost_that_is_not_an_object_of_exactly_amount_currency_and_source_is_refused(
    cost: Any, tmp_path: Path
) -> None:
    """Scenario: a cost that is not an object of exactly amount, currency and
    source is refused."""

    journal_root = tmp_path / "journal"
    # Built with a good cost then replaced — the builder drops a None
    # argument, and the test covers an explicit `null` carried in the
    # record.
    record = _session_with(cost=dict(_COST))
    record["cost"] = cost
    with pytest.raises(JournalRecordError, match="cost"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()
