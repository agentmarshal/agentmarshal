"""Tests for the completed record's advisory dispositions (ADR-0022 s2).

`advisory_dispositions` is the schema-7 field of the `completed` record
type (ADR-0016 decision 1): the recorded choice made for each advisory
finding of the review the gate passed on. It binds by `completed_commit`
alone — `complete --findings` takes no dispositions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.journal import records as records_module
from agentmarshal.journal.records import (
    JournalRecordError,
    create_completed_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)

_COMMIT = "a" * 40
_FINDING_ID = "01J00000000000000000000000"
_DISPOSITIONS = {
    "F-1": {"disposition": "fixed"},
    "F-2": {"disposition": "deferred", "reason": "not this round"},
    "F-3": {"disposition": "rejected", "reason": "not a defect"},
}


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _completed_record(**overrides: Any) -> dict[str, object]:
    record = create_completed_record(
        "CR-001",
        "test",
        _COMMIT,
        advisory_dispositions=dict(_DISPOSITIONS),
    )
    record.update(overrides)
    return record


def _plain_completed() -> dict[str, object]:
    """A completed record carrying none of the family's fields."""

    return create_completed_record("CR-001", "test", _COMMIT)


def _journal_holding(tmp_path: Path, record: dict[str, object]) -> Path:
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    filename = f"{generate_ulid()}-{record['record_type']}.json"
    (records_dir / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path / "journal"


def test_a_completed_record_carrying_advisory_dispositions_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a completed record carrying advisory dispositions is
    written and read back."""

    journal_root = tmp_path / "journal"
    record = create_completed_record(
        "CR-001",
        "test",
        _COMMIT,
        advisory_dispositions={
            "F-1": {"disposition": "fixed", "reason": "already done"},
            "F-2": {
                "disposition": "deferred",
                "reason": "not this round",
                "follow_up": "CR-042",
            },
            "F-3": {"disposition": "rejected", "reason": "not a defect"},
        },
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["advisory_dispositions"] == record["advisory_dispositions"]
    assert stored["schema"] == 7


@pytest.mark.parametrize("dispositions", ["F-1: fixed", ["F-1"], 5, None])
def test_an_advisory_dispositions_that_is_not_an_object_is_refused(
    dispositions: object, tmp_path: Path
) -> None:
    """Scenario: an advisory_dispositions that is not an object is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="advisory_dispositions"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(advisory_dispositions=dispositions),
        )

    assert not journal_root.exists()


def test_an_empty_advisory_dispositions_is_refused(tmp_path: Path) -> None:
    """Scenario: an empty advisory_dispositions is refused.

    A completion with nothing answered carries no `advisory_dispositions`,
    the way `advisory_findings` is omitted when empty — an empty object is
    a second way to say the same thing, refused as a writer's bug.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="advisory_dispositions"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(advisory_dispositions={}),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("finding_id", ["", 5, None])
def test_a_key_that_is_not_a_non_empty_finding_id_is_refused(
    finding_id: object, tmp_path: Path
) -> None:
    """Scenario: a key that is not a non-empty finding id is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="finding id"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={finding_id: {"disposition": "fixed"}}
            ),
        )

    assert not journal_root.exists()


def test_a_finding_id_key_that_could_forge_a_line_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: a finding id key that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(advisory_dispositions={"F\n1": {"disposition": "fixed"}}),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("entry", ["fixed", ["disposition"], 5, None])
def test_a_disposition_entry_that_is_not_an_object_is_refused(
    entry: object, tmp_path: Path
) -> None:
    """Scenario: a disposition entry that is not an object is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*must be an object"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(advisory_dispositions={"F-1": entry}),
        )

    assert not journal_root.exists()


def test_a_disposition_entry_carrying_a_key_that_is_no_disposition_key_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: a disposition entry carrying a key that is no disposition
    key is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*unsupported fields: note"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={"F-1": {"disposition": "fixed", "note": "x"}}
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("disposition", ["wontfix", "done", 5, None])
def test_a_disposition_outside_the_vocabulary_is_refused(
    disposition: object, tmp_path: Path
) -> None:
    """Scenario: a disposition outside the vocabulary is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'disposition'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={"F-1": {"disposition": disposition}}
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("disposition", ["deferred", "rejected"])
def test_a_deferred_or_rejected_disposition_without_a_reason_is_refused(
    disposition: str, tmp_path: Path
) -> None:
    """Scenario: a deferred or rejected disposition without a reason is
    refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'reason'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={"F-1": {"disposition": disposition}}
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("disposition", ["fixed", "deferred", "rejected"])
@pytest.mark.parametrize("reason", ["", "   ", 5, None])
def test_a_reason_that_is_empty_or_not_a_string_is_refused(
    disposition: str, reason: object, tmp_path: Path
) -> None:
    """Scenario: a reason that is empty or not a string is refused.

    Optional on `fixed` but never empty when present: a reason carried is
    a non-empty string on every disposition.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'reason'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={
                    "F-1": {"disposition": disposition, "reason": reason}
                }
            ),
        )

    assert not journal_root.exists()


def test_a_reason_that_could_forge_a_line_is_refused(tmp_path: Path) -> None:
    """Scenario: a reason that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'reason'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={
                    "F-1": {"disposition": "rejected", "reason": "no\ndefect"}
                }
            ),
        )

    assert not journal_root.exists()


def test_a_fixed_disposition_may_carry_a_reason_or_none(tmp_path: Path) -> None:
    """Scenario: a fixed disposition may carry a reason or none."""

    journal_root = tmp_path / "journal"
    write_record(
        journal_root,
        "CR-001",
        _completed_record(
            advisory_dispositions={
                "F-1": {"disposition": "fixed"},
                "F-2": {"disposition": "fixed", "reason": "already done"},
            }
        ),
    )

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["advisory_dispositions"] == {
        "F-1": {"disposition": "fixed"},
        "F-2": {"disposition": "fixed", "reason": "already done"},
    }


def test_a_follow_up_on_a_deferred_disposition_names_a_follow_up_task(
    tmp_path: Path,
) -> None:
    """Scenario: a follow_up on a deferred disposition names a follow-up
    task."""

    journal_root = tmp_path / "journal"
    record = _completed_record(
        advisory_dispositions={
            "F-1": {
                "disposition": "deferred",
                "reason": "not this round",
                "follow_up": "CR-042",
            }
        }
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["advisory_dispositions"] == record["advisory_dispositions"]


@pytest.mark.parametrize("disposition", ["fixed", "rejected"])
def test_a_follow_up_on_a_fixed_or_rejected_disposition_is_refused(
    disposition: str, tmp_path: Path
) -> None:
    """Scenario: a follow_up on a fixed or rejected disposition is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'follow_up'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={
                    "F-1": {
                        "disposition": disposition,
                        "reason": "x",
                        "follow_up": "CR-042",
                    }
                }
            ),
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("follow_up", ["CR-X", "CR-", "CR-1-x", "1", "", 5, None])
def test_a_follow_up_that_is_not_a_task_id_is_refused(
    follow_up: object, tmp_path: Path
) -> None:
    """Scenario: a follow_up that is not a task id is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'follow_up'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={
                    "F-1": {
                        "disposition": "deferred",
                        "reason": "not this round",
                        "follow_up": follow_up,
                    }
                }
            ),
        )

    assert not journal_root.exists()


def test_a_follow_up_that_could_forge_a_line_is_refused(tmp_path: Path) -> None:
    """Scenario: a follow_up that could forge a line is refused.

    The `CR-<number>` shape admits no forgeable character either; the
    forgeable-text check inside the family's rule stands ahead of it, the
    way `accepted_pause`'s `extension` is checked.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"'F-1'.*'follow_up'"):
        write_record(
            journal_root,
            "CR-001",
            _completed_record(
                advisory_dispositions={
                    "F-1": {
                        "disposition": "deferred",
                        "reason": "not this round",
                        "follow_up": "CR-1\nforged",
                    }
                }
            ),
        )

    assert not journal_root.exists()


def test_advisory_dispositions_on_a_finding_bound_completion_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: advisory_dispositions on a finding-bound completion is
    refused.

    The findings lane takes no dispositions (ADR-0016 decision 1): the
    builder refuses up front and the family's rule refuses the record a
    hand-made journal could carry, at write and on read.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="completed_finding"):
        create_completed_record(
            "CR-001",
            "test",
            None,
            completed_finding=_FINDING_ID,
            advisory_dispositions=dict(_DISPOSITIONS),
        )

    record = create_completed_record(
        "CR-001", "test", None, completed_finding=_FINDING_ID
    )
    record["schema"] = 7
    record["advisory_dispositions"] = dict(_DISPOSITIONS)
    with pytest.raises(JournalRecordError, match="completed_finding"):
        write_record(journal_root, "CR-001", record)
    journal_root = _journal_holding(tmp_path, record)
    with pytest.raises(JournalRecordError, match="completed_finding"):
        read_records(journal_root, "CR-001")


def test_a_completed_record_carrying_the_field_stamps_schema_7() -> None:
    """Scenario: a completed record carrying the field stamps schema 7."""

    record = _completed_record()
    assert record["schema"] == 7
    assert record["schema"] == records_module._minimum_schema(record)


def test_the_field_on_a_completed_record_below_schema_7_is_refused_at_write(
    tmp_path: Path,
) -> None:
    """Scenario: the field on a completed record below schema 7 is refused
    at write."""

    journal_root = tmp_path / "journal"
    record = _completed_record()
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_the_field_on_a_completed_record_below_schema_7_is_refused_on_read(
    tmp_path: Path,
) -> None:
    """Scenario: the field on a completed record below schema 7 is refused
    on read."""

    record = _completed_record()
    record["schema"] = 6
    journal_root = _journal_holding(tmp_path, record)
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(journal_root, "CR-001")


def test_a_completed_record_without_the_field_keeps_its_schema_and_reads_as_before(
    tmp_path: Path,
) -> None:
    """Scenario: a completed record without the field keeps its schema and
    reads as before."""

    journal_root = tmp_path / "journal"
    record = _plain_completed()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["schema"] == 3
    assert "advisory_dispositions" not in stored


def test_the_family_is_declared_through_the_schema_7_registrations() -> None:
    """The family registers through the CR-154 mechanism alone: a
    `_FIELD_FAMILIES` entry and the family's own shape rule bound to 7 —
    `advisory_dispositions` is an object of objects, so its `reason` and
    `follow_up` strings take the forgeable-text check inside that rule the
    way `classes` values and `accepted_pause`'s `extension` do, never a
    second mechanism."""

    family = records_module._SCHEMA_7_COMPLETED_FIELDS
    assert family == {"advisory_dispositions"}
    assert (7, "completed", family) in records_module._FIELD_FAMILIES
    assert records_module._RULE_FROM_SCHEMA["completed-fields-7"] == 7


def test_the_gate_path_refuses_a_completed_record_below_7_carrying_the_field() -> None:
    """The gate's own write-side check — `validate_record_content`, run on
    every record a candidate adds — refuses the same records the writer
    does."""

    record = _completed_record()
    record["schema"] = 6
    filename = f"{generate_ulid()}-completed.json"
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        validate_record_content(filename, json.dumps(record))
