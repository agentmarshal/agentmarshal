"""Tests for the acknowledgement record type (ADR-0021, ADR-0022 section 3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_acknowledgement_record,
    create_completed_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from test_journal import initialize_status_repo

_COMMIT = "a" * 40


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    An acknowledgement record requires a resolvable recorder, and the ambient
    `AGENTMARSHAL_ACTOR` must not decide whether a test resolves one —
    every test that needs a recorder names the actor itself.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _acknowledgement_record(**overrides: Any) -> dict[str, object]:
    record = create_acknowledgement_record(
        "CR-001",
        "test",
        _COMMIT,
        "src/app.py",
        "Reviewed: an example key in documentation",
        signature="openai-key",
    )
    record.update(overrides)
    return record


def _without_recorder(record: dict[str, object]) -> dict[str, object]:
    """Drop the stamped actor pair, so a round-trip compares content only."""

    return {
        key: value
        for key, value in record.items()
        if key not in {"recorded_by", "recorded_by_source"}
    }


def test_an_acknowledgement_record_is_written_and_read_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledgement record is written and read back."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _acknowledgement_record()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert _without_recorder(stored) == record | {"id": stored["id"]}
    assert stored["schema"] == 7


def test_a_markers_position_identifies_the_hit_as_well(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a marker's position identifies the hit as well."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = create_acknowledgement_record(
        "CR-001",
        "test",
        _COMMIT,
        "src/<private marker #1>/config",
        "Reviewed: a masked path",
        None,
        marker=1,
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["marker"] == 1
    assert "signature" not in stored


def test_a_record_carrying_both_or_neither_of_signature_and_marker_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a record carrying both or neither of signature and marker is
    refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    both = _acknowledgement_record(marker=1)
    neither = _acknowledgement_record()
    del neither["signature"]
    for record in (both, neither):
        with pytest.raises(JournalRecordError, match=r"'signature'.*'marker'"):
            write_record(journal_root, "CR-001", record)
    with pytest.raises(JournalRecordError, match=r"'signature'.*'marker'"):
        create_acknowledgement_record("CR-001", "t", _COMMIT, "f", "r", None)
    with pytest.raises(JournalRecordError, match=r"'signature'.*'marker'"):
        create_acknowledgement_record(
            "CR-001", "t", _COMMIT, "f", "r", "openai-key", marker=1
        )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "signature", ["not-a-signature", "PRIVATE-KEY-BLOCK", "", 5, None]
)
def test_a_signature_the_scan_does_not_know_is_refused(
    signature: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a signature the scan does not know is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="must be one of"):
        write_record(
            journal_root, "CR-001", _acknowledgement_record(signature=signature)
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("marker", [0, -1, "1", 1.5, True, None])
def test_a_marker_that_is_not_an_integer_of_at_least_1_is_refused(
    marker: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a marker that is not an integer of at least 1 is refused.

    `True` is refused too — a boolean is not the marker's position, however
    Python subclasses it under `int`.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _acknowledgement_record(marker=marker)
    del record["signature"]
    with pytest.raises(JournalRecordError, match="an integer of at least 1"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "commit",
    ["a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + " ", 40, None],
)
def test_a_commit_that_is_not_40_lowercase_hex_is_refused(
    commit: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a commit that is not 40 lowercase hex is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = (
        _acknowledgement_record(commit=commit)
        if commit is not None
        else _acknowledgement_record()
    )
    if commit is None:
        del record["commit"]
    with pytest.raises(JournalRecordError, match=r"40 .*lowercase hex"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("file", ["", "   ", 5, None])
def test_a_file_that_is_missing_or_empty_is_refused(
    file: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a file that is missing or empty is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _acknowledgement_record()
    if file is None:
        del record["file"]
    else:
        record["file"] = file
    with pytest.raises(JournalRecordError, match="non-empty string"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("reason", ["", "   ", 5, None])
def test_a_reason_that_is_missing_or_empty_is_refused(
    reason: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a reason that is missing or empty is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _acknowledgement_record()
    if reason is None:
        del record["reason"]
    else:
        record["reason"] = reason
    with pytest.raises(JournalRecordError, match="non-empty string"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_a_reason_beyond_the_character_bound_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a reason beyond the character bound is refused.

    Characters, not bytes: 1001 'é' characters are past the 1000-character
    bound while a byte count would be past it sooner.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="at most 1000 characters"):
        write_record(journal_root, "CR-001", _acknowledgement_record(reason="é" * 1001))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", ("file", "reason"))
def test_a_displayed_string_that_could_forge_a_line_is_refused(
    field: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a displayed string that could forge a line is refused.

    The two fields register under the forgeable-text rule keyed
    `("acknowledgement", field)` — `commit`'s hex shape, the signature
    vocabulary and `marker`'s integer shape admit no forgeable character,
    so they carry no registration.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(
            journal_root, "CR-001", _acknowledgement_record(**{field: "ok\nforged"})
        )

    assert not journal_root.exists()


def test_an_acknowledgement_record_that_names_no_recorder_is_refused() -> None:
    """Scenario: an acknowledgement record that names no recorder is refused."""

    record = _acknowledgement_record()
    filename = f"{generate_ulid()}-acknowledgement.json"
    with pytest.raises(JournalRecordError, match="resolvable recorder"):
        validate_record_content(filename, json.dumps(record))
    record["recorded_by"] = "an-operator"
    record["recorded_by_source"] = "override"
    assert validate_record_content(filename, json.dumps(record))["recorded_by"] == (
        "an-operator"
    )


def _terminal_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_type: str = "completed",
) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    if record_type == "completed":
        record = create_completed_record("CR-001", "test", _COMMIT)
    else:
        record = create_abandoned_record("CR-001", "test", "Superseded")
    write_record(root, "CR-001", record)
    return repo, root


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_an_acknowledgement_on_a_closed_task_is_refused(
    terminal: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledgement on a closed task is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _repo, root = _terminal_task(tmp_path, monkeypatch, terminal)

    with pytest.raises(TaskStatusError, match="is not open"):
        load_task_for_record(root, "CR-001", "acknowledgement")

    assert main(["validate"]) == 0


def test_an_acknowledgement_record_stamps_schema_7() -> None:
    """Scenario: an acknowledgement record stamps schema 7."""

    record = create_acknowledgement_record(
        "CR-001", "test", _COMMIT, "src/app.py", "r", signature="openai-key"
    )
    assert record["schema"] == 7


def test_an_acknowledgement_record_stamped_below_7_is_refused_at_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledgement record stamped below 7 is refused at
    write.

    An acknowledgement carrying its fields meets the field-admission
    refusal first, as a schema-gated field does; one carrying none of them
    meets the record-type gate. Both are refused before anything is
    written.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _acknowledgement_record()
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    bare = _acknowledgement_record()
    bare["schema"] = 6
    for field in ("commit", "file", "signature", "reason"):
        del bare[field]
    with pytest.raises(JournalRecordError, match="require schema 7"):
        write_record(journal_root, "CR-001", bare)

    assert not journal_root.exists()


def test_an_acknowledgement_record_stamped_below_7_is_refused_on_read(
    tmp_path: Path,
) -> None:
    """Scenario: an acknowledgement record stamped below 7 is refused on
    read."""

    record = _acknowledgement_record()
    record["schema"] = 6
    record["recorded_by"] = "an-operator"
    record["recorded_by_source"] = "override"
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-acknowledgement.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(tmp_path / "journal", "CR-001")

    bare = {
        "schema": 6,
        "record_type": "acknowledgement",
        "task": "CR-001",
        "created_at": "2026-10-03T00:00:00Z",
        "tool_version": "test",
        "source": "live",
        "recorded_by": "an-operator",
        "recorded_by_source": "override",
    }
    bare_dir = tmp_path / "bare-journal" / "tasks" / "CR-001" / "records"
    bare_dir.mkdir(parents=True)
    (bare_dir / f"{generate_ulid()}-acknowledgement.json").write_text(
        json.dumps(bare), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="require schema 7"):
        read_records(tmp_path / "bare-journal", "CR-001")
