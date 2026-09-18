"""Tests for session activity records."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.journal.records import (
    JournalRecordError,
    create_session_record,
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
