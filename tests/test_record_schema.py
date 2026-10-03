"""Read-time rules bound to the schema that introduced them (ADR-0015)."""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from agentmarshal.journal import records as records_module
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_acceptance_record,
    create_amendment_record,
    create_completed_record,
    create_finding_record,
    create_opened_record,
    create_reopened_record,
    create_review_record,
    create_session_record,
    generate_ulid,
    read_records,
    session_record_schema,
    validate_record_content,
    validate_record_for_write,
)

_HIGHEST_SCHEMA = max(records_module._SUPPORTED_SCHEMAS)
_COMMIT = "a" * 40
_HASH = "b" * 64
_REVIEWER = ("qa", "vendor", "model", "r@x.i")


def _opened(schema: int) -> dict[str, object]:
    record = create_opened_record("CR-001", "test")
    if schema < 2:
        record.pop("source")
    record["schema"] = schema
    return record


def _journal_with(tmp_path: Path, record: dict[str, object]) -> Path:
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    filename = f"{generate_ulid()}-{record['record_type']}.json"
    (records_dir / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path / "journal"


def _later_rule(
    monkeypatch: pytest.MonkeyPatch, name: str = "synthetic-later-rule"
) -> None:
    """Register a test-only rule bound to one schema above the highest."""

    def refuse(data: Mapping[str, object], _context: object) -> None:
        raise JournalRecordError("refused by a rule from a later schema")

    monkeypatch.setitem(records_module._RULES, name, refuse)
    monkeypatch.setitem(records_module._RULE_FROM_SCHEMA, name, _HIGHEST_SCHEMA + 1)


def test_every_read_rule_has_its_schema() -> None:
    """Scenario: a rule cannot be checked without an entry in the table.

    The completeness check: a check registered as a rule and absent from the
    table — or an entry naming no rule — fails this test. The schema check
    is not a rule: it runs ahead of the registry, so registering it there
    fails this test too.
    """

    registered: list[object] = list(records_module._RULES.values())
    assert records_module._check_schema_version not in registered
    assert set(records_module._RULES) == set(records_module._RULE_FROM_SCHEMA)


def test_the_schema_check_runs_before_any_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rule registered first still sees a checked schema.

    The schema check is an explicit first step outside the registry, so a
    rule sitting ahead of the others cannot read the schema before it is
    checked: a record with no schema gets the schema error, not the rule's.
    """

    def reads_schema(data: Mapping[str, object], _context: object) -> None:
        if type(data.get("schema")) is not int:
            raise AssertionError("a rule read the schema before it was checked")

    monkeypatch.setattr(
        records_module,
        "_RULES",
        {"reads-schema": reads_schema, **records_module._RULES},
    )
    with pytest.raises(JournalRecordError, match="schema version"):
        validate_record_for_write(
            tmp_path / "journal", "CR-001", {"record_type": "opened"}
        )


def test_a_rule_without_an_entry_is_never_checked_on_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a rule cannot be checked without an entry in the table.

    A rule the table lookup cannot find is skipped on read — it is never
    silently applied to history.
    """

    def refuse(data: Mapping[str, object], _context: object) -> None:
        raise JournalRecordError("a rule without an entry was checked")

    monkeypatch.setitem(records_module._RULES, "unregistered", refuse)
    assert "unregistered" not in records_module._RULE_FROM_SCHEMA

    record = _opened(_HIGHEST_SCHEMA)
    journal_root = _journal_with(tmp_path, record)
    assert read_records(journal_root, "CR-001")[0]["schema"] == _HIGHEST_SCHEMA


def test_todays_rules_apply_from_schema_1_except_the_gates() -> None:
    """Scenario: today's rules apply from schema 1 except the gates bound to
    2, 4, 5 and 6."""

    gates = {
        "provenance": 2,
        "finding-binding": 4,
        "reviewed-contract": 5,
        "coordination": 6,
    }
    for name, schema in records_module._RULE_FROM_SCHEMA.items():
        assert schema == gates.get(name, 1), name


def test_a_record_is_checked_by_every_current_rule_at_write_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a record is checked by every current rule at write time."""

    _later_rule(monkeypatch)
    record = _opened(_HIGHEST_SCHEMA)
    with pytest.raises(JournalRecordError, match="later schema"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    filename = f"{generate_ulid()}-opened.json"
    content = json.dumps(record, ensure_ascii=False)
    with pytest.raises(JournalRecordError, match="later schema"):
        validate_record_content(filename, content)


def test_a_later_rule_does_not_reach_a_record_of_an_earlier_schema_on_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a later rule does not reach a record of an earlier schema on read."""

    _later_rule(monkeypatch)
    record = _opened(_HIGHEST_SCHEMA)
    journal_root = _journal_with(tmp_path, record)
    assert read_records(journal_root, "CR-001")[0]["schema"] == _HIGHEST_SCHEMA


@pytest.mark.parametrize("schema", [1, 2])
def test_a_record_an_earlier_release_wrote_stays_valid(
    tmp_path: Path, schema: int
) -> None:
    """Scenario: a record an earlier release wrote stays valid."""

    journal_root = _journal_with(tmp_path, _opened(schema))
    assert read_records(journal_root, "CR-001")[0]["schema"] == schema


_FINDING_ARTIFACTS = [{"ref": "result.md", "hash": _HASH}]
_FINDING_ID = "01J00000000000000000000000"


@pytest.mark.parametrize(
    "record,expected",
    [
        (create_opened_record("CR-001", "t"), 3),
        (create_completed_record("CR-001", "t", _COMMIT), 3),
        (
            create_completed_record("CR-001", "t", None, completed_finding=_FINDING_ID),
            4,
        ),
        (create_finding_record("CR-001", "t", "s", _FINDING_ARTIFACTS), 4),
        (create_abandoned_record("CR-001", "t", "r"), 3),
        (create_reopened_record("CR-001", "t", "r"), 3),
        (create_amendment_record("CR-001", "t", "r"), 3),
        (
            create_session_record(
                "CR-001", "t", "r", "a", "implementation", "d", 1, 2, 3
            ),
            3,
        ),
        (
            create_session_record(
                "CR-001", "t", "r", "a", "coordination", "d", 1, 2, 3
            ),
            6,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "review",
                "d",
                1,
                2,
                3,
                usage_provider="p",
                usage_method="reported",
            ),
            3,
        ),
        (
            create_review_record("CR-001", "t", _COMMIT, "approved", *_REVIEWER, []),
            3,
        ),
        (
            create_review_record(
                "CR-001",
                "t",
                None,
                "approved",
                *_REVIEWER,
                [],
                reviewed_finding=_FINDING_ID,
            ),
            4,
        ),
        (
            create_review_record(
                "CR-001",
                "t",
                _COMMIT,
                "approved",
                *_REVIEWER,
                [],
                reviewed_contract=_HASH,
            ),
            5,
        ),
        (
            create_review_record(
                "CR-001",
                "t",
                None,
                "approved",
                *_REVIEWER,
                [],
                reviewed_finding=_FINDING_ID,
                reviewed_contract=_HASH,
            ),
            5,
        ),
        (create_acceptance_record("CR-001", "t", _COMMIT, "op", ["F-1"], "r"), 3),
        (
            create_acceptance_record(
                "CR-001",
                "t",
                None,
                "op",
                ["F-1"],
                "r",
                accepted_finding=_FINDING_ID,
            ),
            4,
        ),
    ],
)
def test_each_writer_stamps_the_minimum_schema_its_record_needs(
    record: dict[str, object], expected: int
) -> None:
    """Scenario: each writer stamps the minimum schema its record needs."""

    assert record["schema"] == expected


@pytest.mark.parametrize(
    "activity,expected",
    [
        ("implementation", 3),
        ("review", 3),
        ("other", 3),
        ("coordination", 6),
    ],
)
def test_session_record_schema_uses_the_same_derivation(
    activity: str, expected: int
) -> None:
    """Scenario: each writer stamps the minimum schema its record needs."""

    assert session_record_schema(activity) == expected


def test_a_record_is_checked_against_where_it_lies_on_read(tmp_path: Path) -> None:
    """The placing rules apply on read: the record's task against the task
    directory it lies in."""

    record = create_opened_record("CR-002", "test")
    journal_root = _journal_with(tmp_path, record)
    with pytest.raises(JournalRecordError, match="does not match its directory"):
        read_records(journal_root, "CR-001")


def test_a_record_is_checked_against_its_filename_on_read(tmp_path: Path) -> None:
    """The placing rules apply on read: the record type against the type
    the file name declares."""

    record = create_opened_record("CR-001", "test")
    journal_root = _journal_with(tmp_path, record)
    records_dir = journal_root / "tasks" / "CR-001" / "records"
    (records_dir / f"{generate_ulid()}-review.json").write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="does not match its filename"):
        read_records(journal_root, "CR-001")


def test_a_record_is_checked_against_its_destination_on_write(
    tmp_path: Path,
) -> None:
    """The placing rules apply on write: the record's task against the
    destination it is written to."""

    record = create_opened_record("CR-001", "test")
    with pytest.raises(JournalRecordError, match="does not match its destination"):
        validate_record_for_write(tmp_path / "journal", "CR-002", record)


def test_a_binding_to_an_absent_finding_is_a_write_side_refusal(
    tmp_path: Path,
) -> None:
    """Scenario: a rule comparing a record with where it lies applies where
    the path supplies that placement.

    The task's finding set is the write side's placement input — the author
    can still fix the input — so a completed record bound to a finding the
    task does not hold is refused by validate_record_for_write, while the
    same record already in the journal is read, checked by the rules of its
    own schema.
    """

    record = create_completed_record(
        "CR-001", "test", None, completed_finding=_FINDING_ID
    )
    journal_root = _journal_with(tmp_path, record)
    assert read_records(journal_root, "CR-001")[0]["completed_finding"] == _FINDING_ID
    with pytest.raises(JournalRecordError, match="must name a finding"):
        validate_record_for_write(journal_root, "CR-001", record)
