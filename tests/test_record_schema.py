"""Read-time rules bound to the schema that introduced them (ADR-0015)."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from agentmarshal.journal import records as records_module
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_acceptance_record,
    create_acknowledgement_record,
    create_amendment_record,
    create_check_record,
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
    write_record,
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
    2, 4, 5 and 6.

    The scenario's title names the older gates only — a MODIFIED
    requirement may not rename a scenario — while its THEN also names the
    shared validators bound to 7, which this test pins.
    """

    gates = {
        "provenance": 2,
        "finding-binding": 4,
        "reviewed-contract": 5,
        "coordination": 6,
        "bounded-text": 7,
        "bounded-text-bytes": 7,
        "bounded-json": 7,
        "forgeable-text": 7,
        "session-fields-7": 7,
        "contract-hash-7": 7,
        "check-fields-7": 7,
        "acknowledgement-fields-7": 7,
        "acceptance-fields-7": 7,
        "review-fields-7": 7,
        "completed-fields-7": 7,
    }
    for name, schema in records_module._RULE_FROM_SCHEMA.items():
        assert schema == gates.get(name, 1), name


def test_the_shared_validators_are_their_own_entries_bound_to_7() -> None:
    """Scenario: the shared validators are entries of their own bound to 7.

    A tightening hidden inside a schema-1 rule would apply to old records,
    so each validator is its own entry — never part of another rule.
    """

    for name in (
        "bounded-text",
        "bounded-text-bytes",
        "bounded-json",
        "forgeable-text",
    ):
        assert records_module._RULE_FROM_SCHEMA[name] == 7
        assert name in records_module._RULES


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
            create_completed_record(
                "CR-001",
                "t",
                _COMMIT,
                advisory_dispositions={"F-1": {"disposition": "fixed"}},
            ),
            7,
        ),
        (
            create_completed_record("CR-001", "t", None, completed_finding=_FINDING_ID),
            4,
        ),
        (create_finding_record("CR-001", "t", "s", _FINDING_ARTIFACTS), 4),
        (create_abandoned_record("CR-001", "t", "r"), 3),
        (create_reopened_record("CR-001", "t", "r"), 3),
        (create_amendment_record("CR-001", "t", "r"), 3),
        (create_opened_record("CR-001", "t", contract=_HASH), 7),
        (create_amendment_record("CR-001", "t", "r", contract=_HASH), 7),
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
        (
            create_review_record(
                "CR-001",
                "t",
                _COMMIT,
                "changes_required",
                *_REVIEWER,
                [_FINDING_ID],
                previous_review=_FINDING_ID,
            ),
            7,
        ),
        (
            create_review_record(
                "CR-001",
                "t",
                _COMMIT,
                "changes_required",
                *_REVIEWER,
                [_FINDING_ID],
                classes={_FINDING_ID: "correctness"},
            ),
            7,
        ),
        (
            create_review_record(
                "CR-001",
                "t",
                _COMMIT,
                "approved",
                *_REVIEWER,
                [],
                reviewer_actor="claude",
            ),
            7,
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
        (
            create_acceptance_record(
                "CR-001", "t", _COMMIT, "op", None, "r", accepted_pause="ext"
            ),
            7,
        ),
        (
            create_acceptance_record(
                "CR-001", "t", _COMMIT, "op", None, "r", operational=True
            ),
            7,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "implementation",
                "d",
                1,
                2,
                3,
                commit=_COMMIT,
            ),
            7,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "implementation",
                "d",
                1,
                2,
                3,
                model="m",
            ),
            7,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "implementation",
                "d",
                1,
                2,
                3,
                trace="https://t.example/run",
            ),
            7,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "implementation",
                "d",
                1,
                2,
                3,
                cli_session="c-1",
            ),
            7,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "implementation",
                "d",
                1,
                2,
                3,
                report_ready=True,
            ),
            7,
        ),
        (
            create_session_record(
                "CR-001",
                "t",
                "r",
                "a",
                "coordination",
                "d",
                1,
                2,
                3,
                fallback_reason="fell back",
            ),
            7,
        ),
        (
            create_check_record("CR-001", "t", _COMMIT, "pytest", "passed"),
            7,
        ),
        (
            create_acknowledgement_record(
                "CR-001", "t", _COMMIT, "src/app.py", "r", signature="openai-key"
            ),
            7,
        ),
        (
            create_acknowledgement_record(
                "CR-001", "t", _COMMIT, "src/app.py", "r", None, marker=2
            ),
            7,
        ),
    ],
)
def test_each_writer_stamps_the_minimum_schema_its_record_needs(
    record: dict[str, object], expected: int
) -> None:
    """Scenario: each writer stamps the minimum schema its record needs.

    A record using nothing a schema introduced stamps below that schema:
    the session fields of schema 7 are what raises a session's stamp to 7.
    The second assertion re-derives the stamp from the record's own fields
    — a writer stamping a hand-chosen number fails it.
    """

    assert record["schema"] == expected
    assert record["schema"] == records_module._minimum_schema(record)


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


def test_no_writer_stamps_a_schema_no_field_needs() -> None:
    """Scenario: no writer stamps a schema no field needs.

    A record carrying no field a schema-7 family admits keeps the stamp it
    always had — the family existing does not lift a record that uses none
    of it.
    """

    records = [
        create_opened_record("CR-001", "t"),
        create_completed_record("CR-001", "t", _COMMIT),
        create_abandoned_record("CR-001", "t", "r"),
        create_review_record("CR-001", "t", _COMMIT, "approved", *_REVIEWER, []),
        create_acceptance_record("CR-001", "t", _COMMIT, "op", ["F-1"], "r"),
        create_session_record("CR-001", "t", "r", "a", "implementation", "d", 1, 2, 3),
        create_session_record("CR-001", "t", "r", "a", "coordination", "d", 1, 2, 3),
    ]
    for record in records:
        assert cast(int, record["schema"]) < 7, record
    assert session_record_schema("coordination") < 7


def test_a_writer_stamps_schema_7_when_its_record_needs_it() -> None:
    """Scenario: a writer stamps schema 7 when its record needs it.

    Each field of the family — `report_ready` included, on the `False`
    that is a value carried rather than a field omitted — raises the
    session's stamp to 7 through the one derivation.
    """

    family: tuple[tuple[str, Any], ...] = (
        ("commit", _COMMIT),
        ("model", "m"),
        ("trace", "https://t.example/run"),
        ("cli_session", "c-1"),
        ("report_ready", False),
        ("fallback_reason", "fell back"),
    )
    for field, value in family:
        record = create_session_record(
            "CR-001",
            "t",
            "r",
            "a",
            "implementation",
            "d",
            1,
            2,
            3,
            **{field: value},
        )
        assert record["schema"] == 7, field


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


# --- schema 7 and the shared field validators (ADR-0022 section 8) --------

_TEST_FIELD = "test_field"


def _admit_test_field(
    monkeypatch: pytest.MonkeyPatch,
    from_schema: int = _HIGHEST_SCHEMA,
    fields: tuple[str, ...] = (_TEST_FIELD,),
) -> None:
    """Admit test-only fields from *from_schema*, as a field family would."""

    monkeypatch.setattr(
        records_module,
        "_FIELD_FAMILIES",
        (
            *records_module._FIELD_FAMILIES,
            (from_schema, None, frozenset(fields)),
        ),
    )


def test_a_schema_7_record_with_only_older_fields_round_trips(
    tmp_path: Path,
) -> None:
    """Scenario: a record of the newest schema carrying only fields older
    schemas allow is written and read."""

    assert _HIGHEST_SCHEMA == 7
    record = _opened(_HIGHEST_SCHEMA)
    write_record(tmp_path / "journal", "CR-001", record)
    stored = read_records(tmp_path / "journal", "CR-001")[0]
    assert {
        key: value
        for key, value in stored.items()
        if key not in {"id", "recorded_by", "recorded_by_source"}
    } == record


def test_bounded_text_refuses_a_value_over_its_character_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a registered text field over its character bound is refused."""

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._TEXT_CHAR_LIMITS, ("opened", _TEST_FIELD), 4)
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: "xxxxx"}
    with pytest.raises(JournalRecordError, match="at most 4 characters"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    # A non-string is not a bounded text either.
    record[_TEST_FIELD] = 5
    with pytest.raises(JournalRecordError, match="a string of at most"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_bounded_text_bytes_refuses_a_value_over_its_byte_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a registered text field over its byte bound is refused.

    Bytes, not characters: ADR-0022 bounds `excerpt` at 4 KiB, and three
    'é' characters are six UTF-8 bytes — over a bound a character count
    would pass.
    """

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._TEXT_BYTE_LIMITS, ("opened", _TEST_FIELD), 4)
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: "ééé"}
    with pytest.raises(JournalRecordError, match="at most 4 UTF-8 bytes"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    # A non-string is not a bounded text either.
    record[_TEST_FIELD] = 5
    with pytest.raises(JournalRecordError, match="a string of at most"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_bounded_json_refuses_a_value_over_its_canonical_byte_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a registered JSON field over its canonical byte bound is
    refused.

    The canonical encoding decides the count — sorted keys, compact
    separators, UTF-8 — not the spacing the record happened to carry.
    """

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._JSON_BYTE_LIMITS, ("opened", _TEST_FIELD), 13)
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: {"key": "x" * 20}}
    with pytest.raises(JournalRecordError, match="at most 13 bytes"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    # `{"b": 1, "a": 2}` encodes canonically to `{"a":2,"b":1}` — 13 bytes.
    record[_TEST_FIELD] = {"b": 1, "a": 2}
    data = validate_record_for_write(tmp_path / "journal", "CR-001", record)
    assert data[_TEST_FIELD] == {"b": 1, "a": 2}
    # A value JSON cannot encode is refused rather than crashing the rule.
    record[_TEST_FIELD] = {1, 2}
    with pytest.raises(JournalRecordError, match="must be a JSON value"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_bounded_json_refuses_a_non_finite_float(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """NaN and Infinity are not JSON, so the rule refuses them as such.

    ``json.loads`` reads the ``NaN``/``Infinity`` tokens a hand-edited
    record file may carry; the canonical encoding refuses them
    (``allow_nan=False``) rather than emitting the same non-JSON token
    back, so the record gets the rule's "must be a JSON value" refusal —
    at write, and at read for a file already holding the token.
    """

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._JSON_BYTE_LIMITS, ("opened", _TEST_FIELD), 13)
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: {"key": float("inf")}}
    with pytest.raises(JournalRecordError, match="must be a JSON value"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    journal_root = _journal_with(tmp_path, record | {_TEST_FIELD: float("nan")})
    with pytest.raises(JournalRecordError, match="must be a JSON value"):
        read_records(journal_root, "CR-001")


def test_forgeable_text_refuses_a_registered_field_carrying_a_non_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registered field whose value is not a string is refused, not
    skipped.

    The rule is fail-closed like its sibling bounded-text: a registration
    that names a non-string field meets a refusal, not silent passage —
    the field may carry no shape rule of its own to own the type.
    """

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(
        records_module._FORGEABLE_TEXT_FIELDS, ("opened", _TEST_FIELD), None
    )
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: ["not", "text"]}
    with pytest.raises(JournalRecordError, match="must be a string"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_forgeable_text_refuses_a_displayed_string_that_could_forge_a_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a registered displayed string that could forge a line is
    refused."""

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(
        records_module._FORGEABLE_TEXT_FIELDS, ("opened", _TEST_FIELD), None
    )
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: "line one\nline two"}
    with pytest.raises(JournalRecordError, match="control characters"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    record[_TEST_FIELD] = "reorder\u202eme"
    with pytest.raises(JournalRecordError, match="control characters"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_a_registered_field_within_its_bounds_is_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a registered field within its bounds is admitted."""

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._TEXT_CHAR_LIMITS, ("opened", _TEST_FIELD), 4)
    monkeypatch.setitem(records_module._TEXT_BYTE_LIMITS, ("opened", _TEST_FIELD), 4)
    monkeypatch.setitem(records_module._JSON_BYTE_LIMITS, ("opened", _TEST_FIELD), 12)
    monkeypatch.setitem(
        records_module._FORGEABLE_TEXT_FIELDS, ("opened", _TEST_FIELD), None
    )
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: "xxxx"}
    data = validate_record_for_write(tmp_path / "journal", "CR-001", record)
    assert data[_TEST_FIELD] == "xxxx"
    journal_root = _journal_with(tmp_path, record)
    assert read_records(journal_root, "CR-001")[0][_TEST_FIELD] == "xxxx"
    # Two 'é' characters are exactly four UTF-8 bytes — inside the byte
    # bound while a shorter character count would also pass.
    record[_TEST_FIELD] = "éé"
    data = validate_record_for_write(tmp_path / "journal", "CR-001", record)
    assert data[_TEST_FIELD] == "éé"


def test_a_schema_7_validator_does_not_reach_an_earlier_record_on_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a schema-7 validator does not reach a record of an earlier
    schema on read.

    The field is admitted from schema 3 while the validator stays bound to
    7: the same over-bound value is refused at write, where the author can
    still fix the input, and left alone on read.
    """

    _admit_test_field(monkeypatch, from_schema=3)
    monkeypatch.setitem(records_module._TEXT_CHAR_LIMITS, ("opened", _TEST_FIELD), 4)
    record = _opened(3) | {_TEST_FIELD: "xxxxx"}
    with pytest.raises(JournalRecordError, match="at most 4 characters"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
    journal_root = _journal_with(tmp_path, record)
    assert read_records(journal_root, "CR-001")[0][_TEST_FIELD] == "xxxxx"


def test_a_bound_on_one_types_field_leaves_another_types_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bound keys on the record type, not the field name alone.

    ADR-0022's ``reason`` bound is for the new record types alone, and the
    name is already taken: a registration keyed by field name only could
    not keep it off the ``reason`` fields older record types carry. A
    bound registered for one type's field must not reach another type's
    field of the same name — at write, where every rule applies.
    """

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._TEXT_CHAR_LIMITS, ("session", _TEST_FIELD), 4)
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: "xxxxx"}
    data = validate_record_for_write(tmp_path / "journal", "CR-001", record)
    assert data[_TEST_FIELD] == "xxxxx"
    # The same field name on the type the registration names is guarded.
    monkeypatch.setitem(records_module._TEXT_CHAR_LIMITS, ("opened", _TEST_FIELD), 4)
    with pytest.raises(JournalRecordError, match="at most 4 characters"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_the_every_type_registration_guards_the_field_on_every_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``None`` in the record-type slot guards the field wherever it lies.

    The explicit "every type" form exists for a field the rule guards on
    every record type that carries it — never for a name an older record
    type already has.
    """

    _admit_test_field(monkeypatch)
    monkeypatch.setitem(records_module._JSON_BYTE_LIMITS, (None, _TEST_FIELD), 13)
    record = _opened(_HIGHEST_SCHEMA) | {_TEST_FIELD: {"key": "x" * 20}}
    with pytest.raises(JournalRecordError, match="at most 13 bytes"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)


def test_forgeable_text_reports_fields_in_registration_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The field a refusal names is stable run to run.

    The table iterates in registration order; iterated as a set it would
    name whichever field string-hash order happened to yield first.
    """

    _admit_test_field(monkeypatch, fields=("zzz_field", "aaa_field"))
    monkeypatch.setattr(
        records_module,
        "_FORGEABLE_TEXT_FIELDS",
        {("opened", "zzz_field"): None, ("opened", "aaa_field"): None},
    )
    record = _opened(_HIGHEST_SCHEMA) | {
        "aaa_field": "forge\nable",
        "zzz_field": "also forge\nable",
    }
    with pytest.raises(JournalRecordError, match="'zzz_field'"):
        validate_record_for_write(tmp_path / "journal", "CR-001", record)
