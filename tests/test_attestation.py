"""Tests for the record-type registry, attestation vocabulary and schema-2+ records."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import get_args

import pytest

from agentmarshal.journal import status as status_module
from agentmarshal.journal.attestation import (
    PREDICATE_TYPES,
    RECORD_TYPES,
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
    validate_record_content,
    write_record,
)

_HEX64 = "a" * 64


def _opened_v2(*, schema: int = 2, **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": schema,
        "record_type": "opened",
        "task": "CR-001",
        "created_at": "2026-07-19T00:00:00Z",
        "tool_version": "1.0",
        "source": SOURCE_LIVE,
    }
    record.update(overrides)
    return record


# --- registry -------------------------------------------------------------


def _without_recorder(record: dict[str, object]) -> dict[str, object]:
    """Drop the stamped actor pair, so a round-trip compares content only.

    write_record stamps recorded_by/recorded_by_source from the invoking
    identity (ADR-0006), which varies by machine. These assertions are about the
    record surviving the round trip unchanged, not about who wrote it.
    """

    return {
        key: value
        for key, value in record.items()
        if key not in {"recorded_by", "recorded_by_source"}
    }


def test_predicate_type_for_returns_registered_uri() -> None:
    assert predicate_type_for("review") == PREDICATE_TYPES["review"]
    assert predicate_type_for("completed").startswith("https://agentmarshal.dev/")
    assert predicate_type_for("amendment").endswith("/amendment/v1")


def test_predicate_type_for_unregistered_fails_closed() -> None:
    with pytest.raises(UnknownPredicateTypeError):
        predicate_type_for("nope")
    assert not is_registered_record_type("nope")


def test_every_accepted_record_type_is_registered() -> None:
    # The completeness check depends on this coupling: a record type the
    # validator accepts must be projectable to an in-toto Statement.
    assert set(_RECORD_FIELDS) == set(PREDICATE_TYPES)


def test_the_three_modules_read_the_one_registry() -> None:
    """Scenario: the three modules read the one registry.

    The derived surfaces are pinned against literals, not recomputed from
    the registry — a shared drift of registry and derivation cannot pass
    this test. The writable Literal is pinned the same way, since a
    Literal cannot be derived at type-check time.
    """

    assert PREDICATE_TYPES == {
        "opened": "https://agentmarshal.dev/attestations/opening/v1",
        "review": "https://agentmarshal.dev/attestations/review/v1",
        "acceptance": "https://agentmarshal.dev/attestations/acceptance/v1",
        "completed": "https://agentmarshal.dev/attestations/completion/v1",
        "abandoned": "https://agentmarshal.dev/attestations/abandonment/v1",
        "reopened": "https://agentmarshal.dev/attestations/reopening/v1",
        "amendment": "https://agentmarshal.dev/attestations/amendment/v1",
        "session": "https://agentmarshal.dev/attestations/session/v1",
        "finding": "https://agentmarshal.dev/attestations/finding/v1",
        "check": "https://agentmarshal.dev/attestations/check/v1",
        "agreement": "https://agentmarshal.dev/attestations/agreement/v1",
        "acknowledgement": "https://agentmarshal.dev/attestations/acknowledgement/v1",
    }
    assert dict(status_module._RECORD_TYPE_STATES) == {
        "opened": "open",
        "review": None,
        "acceptance": None,
        "completed": "done",
        "abandoned": "abandoned",
        "reopened": "open",
        "amendment": None,
        "session": None,
        "finding": None,
        "check": None,
        "agreement": None,
        "acknowledgement": None,
    }
    terminal = {"completed", "abandoned"}
    assert terminal == status_module._TERMINAL_RECORD_TYPES
    admitted_after_terminal = {"reopened", "session", "check"}
    assert (
        admitted_after_terminal == status_module._RECORD_TYPES_ADMITTED_AFTER_TERMINAL
    )
    writable = {
        "opened",
        "review",
        "acceptance",
        "session",
        "amendment",
        "finding",
        "completed",
        "abandoned",
        "reopened",
        "check",
        "agreement",
        "acknowledgement",
    }
    assert writable == status_module._WRITABLE_RECORD_TYPES
    assert set(get_args(status_module.WritableRecordType)) == writable
    # The admission rule reads the registry's own per-type state sets.
    admitted = {
        ("reopened", "done"),
        ("session", "done"),
        ("session", "abandoned"),
        ("check", "done"),
        ("check", "abandoned"),
    }
    for record_type in PREDICATE_TYPES:
        for terminal_state in ("done", "abandoned"):
            assert status_module.record_type_is_admitted_after_terminal(
                record_type, terminal_state
            ) == ((record_type, terminal_state) in admitted)
    assert {
        record_type
        for record_type, spec in RECORD_TYPES.items()
        if spec.requires_recorded_by
    } == {"finding", "check", "agreement", "acknowledgement"}


def test_the_writable_flag_is_what_the_write_path_consults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A type the registry marks not writable cannot be written.

    The guard is not the flag's only reader — write_record behind
    validate_record_for_write, and the gate's validate_record_content over
    a record a candidate adds, refuse the same type — while a record of it
    already in the journal still reads: the flag decides creation, never
    history.
    """

    monkeypatch.setitem(
        RECORD_TYPES, "opened", replace(RECORD_TYPES["opened"], writable=False)
    )
    record = _opened_v2()
    filename = "01J00000000000000000000000-opened.json"
    with pytest.raises(JournalRecordError, match="not writable"):
        write_record(tmp_path / "journal", "CR-001", record)
    with pytest.raises(JournalRecordError, match="not writable"):
        validate_record_content(filename, json.dumps(record))
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / filename).write_text(json.dumps(record), encoding="utf-8")
    assert read_records(tmp_path / "journal", "CR-001")[0]["record_type"] == "opened"


def test_a_type_requiring_its_recorder_refuses_a_record_naming_none() -> None:
    """Scenario: a type that requires its recorder refuses a record that
    names none.

    `finding` is the type the flag covers today; the requirement moved
    from an inline check onto the registry flag with the same refusal.
    """

    assert RECORD_TYPES["finding"].requires_recorded_by
    record: dict[str, object] = {
        "schema": 4,
        "record_type": "finding",
        "task": "CR-001",
        "created_at": "2026-07-19T00:00:00Z",
        "tool_version": "1.0",
        "source": SOURCE_LIVE,
        "summary": "a finding",
        "artifacts": [{"ref": "result.md", "hash": _HEX64}],
    }
    filename = "01J00000000000000000000000-finding.json"
    with pytest.raises(JournalRecordError, match="resolvable recorder"):
        validate_record_content(filename, json.dumps(record))
    record["recorded_by"] = "an-agent"
    record["recorded_by_source"] = "override"
    assert validate_record_content(filename, json.dumps(record))["recorded_by"] == (
        "an-agent"
    )


# --- schema-2+ acceptance -------------------------------------------------


@pytest.mark.parametrize("schema", [2, 3])
def test_schema_2_plus_round_trip_with_source_and_artifacts(
    tmp_path: Path, schema: int
) -> None:
    root = tmp_path / "journal"
    record = _opened_v2(
        schema=schema,
        source=SOURCE_IMPORTED,
        artifacts=[{"ref": "runs/CR-001-prompt.md", "hash": _HEX64}],
    )
    identifier = "01J00000000000000000000000"
    write_record(root, "CR-001", record, record_id=identifier)
    assert [_without_recorder(r) for r in read_records(root, "CR-001")] == [
        record | {"id": identifier}
    ]


@pytest.mark.parametrize("schema", [2, 3])
def test_schema_2_plus_without_artifacts_is_valid(tmp_path: Path, schema: int) -> None:
    root = tmp_path / "journal"
    write_record(
        root,
        "CR-001",
        _opened_v2(schema=schema),
        record_id="01J00000000000000000000001",
    )
    stored = read_records(root, "CR-001")
    assert stored[0]["source"] == SOURCE_LIVE
    assert "artifacts" not in stored[0]


# --- schema-2+ rejections -------------------------------------------------


@pytest.mark.parametrize("schema", [2, 3])
def test_schema_2_plus_without_source_is_rejected(tmp_path: Path, schema: int) -> None:
    record = _opened_v2(schema=schema)
    del record["source"]
    with pytest.raises(JournalRecordError, match="source"):
        write_record(tmp_path / "journal", "CR-001", record)


@pytest.mark.parametrize("schema", [2, 3])
def test_schema_2_plus_bad_source_is_rejected(tmp_path: Path, schema: int) -> None:
    with pytest.raises(JournalRecordError, match="source"):
        write_record(
            tmp_path / "journal",
            "CR-001",
            _opened_v2(schema=schema, source="fabricated"),
        )


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
@pytest.mark.parametrize("schema", [2, 3])
def test_schema_2_plus_malformed_artifacts_are_rejected(
    tmp_path: Path, artifacts: object, schema: int
) -> None:
    with pytest.raises(JournalRecordError):
        write_record(
            tmp_path / "journal",
            "CR-001",
            _opened_v2(schema=schema, artifacts=artifacts),
        )


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
    """Scenario: the schema above the newest is unknown and refused.

    The number moves as the ladder grows — schema 7 is known now, so the
    unknown example is 8 — what is pinned is the refusal, at write and at
    read.
    """

    record = _opened_v2(schema=8)
    with pytest.raises(JournalRecordError, match="schema"):
        write_record(tmp_path / "journal", "CR-001", record)
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / "01J00000000000000000000000-opened.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="schema"):
        read_records(tmp_path / "journal", "CR-001")
