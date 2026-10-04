"""Tests for the review record's verification and evidence fields (ADR-0022 s2).

`verification` — what the reviewer executed, read and could not run
(ADR-0017 decision 4) — and `evidence` — a reference behind each finding
the record names (ADR-0017 decision 5) — are top-level fields of the
schema-7 review family.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.journal import records as records_module
from agentmarshal.journal.records import (
    JournalRecordError,
    create_review_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)

_COMMIT = "a" * 40
_REVIEWER = ("qa", "vendor", "model", "r@x.i")
_FINDING_1 = "01J00000000000000000000001"
_FINDING_2 = "01J00000000000000000000002"
_ADVISORY = "01J0000000000000000000000A"
_VERIFICATION = {
    "executed": [
        {"what": "uv run pytest -q", "result": "42 passed"},
        {"what": "uv run ruff check", "result": "clean"},
    ],
    "read": ["src/agentmarshal/journal/records.py"],
    "not_run": [{"what": "uv run mypy", "why": "no type stubs installed"}],
}
_EVIDENCE = {
    _FINDING_1: "src/agentmarshal/journal/records.py:1042",
    _ADVISORY: "uv run pytest -q — 42 passed",
}


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _review_record(**overrides: Any) -> dict[str, object]:
    record = create_review_record(
        "CR-001",
        "test",
        _COMMIT,
        "changes_required",
        *_REVIEWER,
        [_FINDING_1, _FINDING_2],
        advisory_findings=[_ADVISORY],
        verification=dict(_VERIFICATION),
        evidence=dict(_EVIDENCE),
    )
    record.update(overrides)
    return record


def _plain_review() -> dict[str, object]:
    """A review record carrying neither of the two fields."""

    return create_review_record(
        "CR-001", "test", _COMMIT, "changes_required", *_REVIEWER, [_FINDING_1]
    )


def _journal_holding(tmp_path: Path, record: dict[str, object]) -> Path:
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    filename = f"{generate_ulid()}-{record['record_type']}.json"
    (records_dir / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path / "journal"


_FIELDS = ("verification", "evidence")


def _carrying(record: dict[str, object], field: str) -> dict[str, object]:
    """Add one of the two fields to a plain review record."""

    if field == "verification":
        record["verification"] = {"executed": [{"what": "w", "result": "r"}]}
    else:
        record["evidence"] = {_FINDING_1: "src/x.py:1"}
    return record


def test_a_review_carrying_verification_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a review carrying verification is written and read back."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _review_record())

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["verification"] == _VERIFICATION
    assert stored["schema"] == 7


@pytest.mark.parametrize("verification", ["executed", [_COMMIT], 5])
def test_a_verification_that_is_not_an_object_is_refused(
    verification: object, tmp_path: Path
) -> None:
    """Scenario: a verification that is not an object is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="verification"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


def test_an_empty_verification_object_is_refused(tmp_path: Path) -> None:
    """Scenario: an empty verification object is refused.

    A review with nothing executed, read or left unrun carries no
    `verification` — an empty object is a second way to say the same
    thing, refused as a writer's bug.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="verification"):
        write_record(journal_root, "CR-001", _review_record(verification={}))

    assert not journal_root.exists()


@pytest.mark.parametrize("key", ["skipped", "RAN", "executed2"])
def test_a_verification_carrying_a_key_outside_the_three_is_refused(
    key: str, tmp_path: Path
) -> None:
    """Scenario: a verification carrying a key outside the three is refused."""

    journal_root = tmp_path / "journal"
    verification = {"executed": [{"what": "w", "result": "r"}], key: ["x"]}
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "verification",
    [
        {"executed": []},
        {"read": "src/x.py"},
        {"not_run": {"what": "w", "why": "y"}},
    ],
)
def test_a_verification_section_that_is_not_a_non_empty_array_is_refused(
    verification: dict[str, object], tmp_path: Path
) -> None:
    """Scenario: a verification section that is not a non-empty array is
    refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="non-empty array"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "entry",
    [
        {"what": "w"},
        {"what": "w", "result": "r", "how": "h"},
        {"result": "r"},
        "uv run pytest",
        5,
    ],
)
def test_an_executed_entry_missing_a_key_or_carrying_another_is_refused(
    entry: object, tmp_path: Path
) -> None:
    """Scenario: an executed entry missing a key or carrying another is
    refused."""

    journal_root = tmp_path / "journal"
    verification = {"executed": [entry]}
    with pytest.raises(JournalRecordError, match="executed"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "entry",
    [
        {"what": "w"},
        {"what": "w", "why": "y", "result": "r"},
        {"why": "y"},
        "could not run",
        5,
    ],
)
def test_a_not_run_entry_missing_a_key_or_carrying_another_is_refused(
    entry: object, tmp_path: Path
) -> None:
    """Scenario: a not_run entry missing a key or carrying another is
    refused."""

    journal_root = tmp_path / "journal"
    verification = {"not_run": [entry]}
    with pytest.raises(JournalRecordError, match="not_run"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "verification",
    [
        {"read": ["ok", 5]},
        {"read": ["ok", "   "]},
        {"executed": [{"what": "", "result": "r"}]},
        {"executed": [{"what": "w", "result": 5}]},
        {"not_run": [{"what": "w", "why": " "}]},
        {"not_run": [{"what": None, "why": "y"}]},
    ],
)
def test_a_verification_string_that_is_empty_or_not_a_string_is_refused(
    verification: dict[str, object], tmp_path: Path
) -> None:
    """Scenario: a verification string that is empty or not a string is
    refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="non-empty string"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "verification",
    [
        {"read": ["ok\nforged"]},
        {"executed": [{"what": "w", "result": "reorder\u202eme"}]},
        {"not_run": [{"what": "w", "why": "two\nlines"}]},
    ],
)
def test_a_verification_string_that_could_forge_a_line_is_refused(
    verification: dict[str, object], tmp_path: Path
) -> None:
    """Scenario: a verification string that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    assert not journal_root.exists()


def test_a_verification_refusal_names_the_key_and_the_position_at_fault(
    tmp_path: Path,
) -> None:
    """Scenario: a refusal names the key and the position at fault."""

    journal_root = tmp_path / "journal"
    verification = {
        "executed": [
            {"what": "w", "result": "r"},
            {"what": "w", "result": ""},
        ]
    }
    with pytest.raises(JournalRecordError) as error:
        write_record(journal_root, "CR-001", _review_record(verification=verification))

    message = str(error.value)
    assert "'executed'" in message
    assert "entry 1" in message
    assert "'result'" in message


def test_a_review_carrying_evidence_for_its_findings_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a review carrying evidence for its findings is written and
    read back."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _review_record())

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["evidence"] == _EVIDENCE
    assert stored["schema"] == 7


@pytest.mark.parametrize(
    "evidence",
    [
        {"01J00000000000000000000009": "a link"},
        {_FINDING_1: "src/x.py:1", "F-9": "another link"},
    ],
)
def test_an_evidence_key_naming_no_finding_of_the_record_is_refused(
    evidence: dict[str, str], tmp_path: Path
) -> None:
    """Scenario: an evidence key naming no finding of the record is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="evidence"):
        write_record(journal_root, "CR-001", _review_record(evidence=evidence))

    assert not journal_root.exists()


def test_an_empty_evidence_object_is_refused(tmp_path: Path) -> None:
    """Scenario: an empty evidence object is refused.

    A review with no evidence to name carries no `evidence` — an empty
    object is a second way to say the same thing, refused as a writer's
    bug.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="evidence"):
        write_record(journal_root, "CR-001", _review_record(evidence={}))

    assert not journal_root.exists()


@pytest.mark.parametrize("evidence", ["a link", [_FINDING_1], 5])
def test_an_evidence_that_is_not_an_object_is_refused(
    evidence: object, tmp_path: Path
) -> None:
    """Scenario: an evidence that is not an object is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="evidence"):
        write_record(journal_root, "CR-001", _review_record(evidence=evidence))

    assert not journal_root.exists()


@pytest.mark.parametrize("value", ["", "   ", 5, None])
def test_an_evidence_value_that_is_empty_or_not_a_string_is_refused(
    value: object, tmp_path: Path
) -> None:
    """Scenario: an evidence value that is empty or not a string is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="evidence"):
        write_record(
            journal_root,
            "CR-001",
            _review_record(evidence={_FINDING_1: value}),
        )

    assert not journal_root.exists()


def test_an_evidence_value_that_could_forge_a_line_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: an evidence value that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(
            journal_root,
            "CR-001",
            _review_record(evidence={_FINDING_1: "ok\nforged"}),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("field", _FIELDS)
def test_a_review_carrying_either_field_stamps_schema_7(field: str) -> None:
    """Scenario: a review carrying either field stamps schema 7."""

    assert records_module._minimum_schema(_carrying(_plain_review(), field)) == 7


@pytest.mark.parametrize("field", _FIELDS)
def test_either_field_on_a_review_below_schema_7_is_refused_at_write(
    field: str, tmp_path: Path
) -> None:
    """Scenario: either field on a review below schema 7 is refused at
    write."""

    journal_root = tmp_path / "journal"
    record = _plain_review()
    record["schema"] = 6
    with pytest.raises(JournalRecordError):
        write_record(journal_root, "CR-001", _carrying(record, field))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", _FIELDS)
def test_either_field_on_a_review_below_schema_7_is_refused_on_read(
    field: str, tmp_path: Path
) -> None:
    """Scenario: either field on a review below schema 7 is refused on
    read.

    Both are top-level fields, so they meet the field-admission rule of
    the record's own schema — the `fields` rule is bound to 1 and the
    read side refuses them exactly as the writer does.
    """

    record = _plain_review()
    record["schema"] = 6
    journal_root = _journal_holding(tmp_path, _carrying(record, field))
    with pytest.raises(JournalRecordError):
        read_records(journal_root, "CR-001")


def test_a_review_carrying_neither_field_keeps_its_schema_and_reads_as_before(
    tmp_path: Path,
) -> None:
    """Scenario: a review carrying neither field keeps its schema and reads
    as before."""

    journal_root = tmp_path / "journal"
    record = _plain_review()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["schema"] == 3
    assert "verification" not in stored
    assert "evidence" not in stored


def test_the_fields_register_through_the_schema_7_mechanism() -> None:
    """The two fields join the family's CR-154 registrations: the
    `_FIELD_FAMILIES` entry's frozenset and the minimum-schema derivation.
    Both are objects, so the forgeable-text table holds no entry for them
    — a table entry would fail-closed on the dict — and their nested
    strings take the check inside the family's own rule."""

    family = records_module._SCHEMA_7_REVIEW_FIELDS
    assert {"verification", "evidence"} <= family
    assert (7, "review", family) in records_module._FIELD_FAMILIES
    assert ("review", "verification") not in records_module._FORGEABLE_TEXT_FIELDS
    assert ("review", "evidence") not in records_module._FORGEABLE_TEXT_FIELDS
    assert records_module._RULE_FROM_SCHEMA["review-fields-7"] == 7


def test_the_gate_path_refuses_a_review_below_7_carrying_either_field() -> None:
    """The gate's own write-side check — `validate_record_content`, run on
    every record a candidate adds — refuses the same records the writer
    does."""

    record = _review_record()
    record["schema"] = 6
    filename = f"{generate_ulid()}-review.json"
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        validate_record_content(filename, json.dumps(record))
