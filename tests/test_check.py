"""Tests for the check record type (ADR-0017 decision 1, ADR-0022 section 3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_check_record,
    create_completed_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.journal.status import load_task_for_record
from test_journal import initialize_status_repo

_COMMIT = "a" * 40


def _check_record(**overrides: Any) -> dict[str, object]:
    record = create_check_record(
        "CR-001",
        "test",
        _COMMIT,
        "unit-tests",
        "failed",
        failed_step="tests",
        excerpt="test_x failed",
        run_url="https://ci.example/run/1",
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


def test_a_check_record_is_written_and_read_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a check record is written and read back."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    journal_root = tmp_path / "journal"
    record = _check_record()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert _without_recorder(stored) == record | {"id": stored["id"]}
    assert stored["schema"] == 7


def test_the_optional_fields_may_be_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the optional fields may be absent."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    journal_root = tmp_path / "journal"
    write_record(
        journal_root,
        "CR-001",
        create_check_record("CR-001", "test", _COMMIT, "unit-tests", "passed"),
    )

    stored = read_records(journal_root, "CR-001")[0]
    for field in ("failed_step", "excerpt", "run_url"):
        assert field not in stored


@pytest.mark.parametrize(
    "commit",
    ["a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + " ", 40, None],
)
def test_a_commit_that_is_not_40_lowercase_hex_is_refused(
    commit: object, tmp_path: Path
) -> None:
    """Scenario: a commit that is not 40 lowercase hex is refused."""

    journal_root = tmp_path / "journal"
    record = _check_record(commit=commit) if commit is not None else _check_record()
    if commit is None:
        del record["commit"]
    with pytest.raises(JournalRecordError, match=r"40 .*lowercase hex"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("name", ["", "   ", 5, None])
def test_a_name_that_is_missing_or_empty_is_refused(
    name: object, tmp_path: Path
) -> None:
    """Scenario: a name that is missing or empty is refused."""

    journal_root = tmp_path / "journal"
    record = _check_record()
    if name is None:
        del record["name"]
    else:
        record["name"] = name
    with pytest.raises(JournalRecordError, match="non-empty string"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("result", ["success", "", 5, None])
def test_a_result_outside_the_outcome_vocabulary_is_refused(
    result: object, tmp_path: Path
) -> None:
    """Scenario: a result outside the outcome vocabulary is refused."""

    journal_root = tmp_path / "journal"
    record = _check_record()
    if result is None:
        del record["result"]
    else:
        record["result"] = result
    with pytest.raises(JournalRecordError, match="must be one of"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("field", ("failed_step", "excerpt", "run_url"))
@pytest.mark.parametrize("value", ["", "   ", 5])
def test_an_optional_field_that_is_empty_is_refused(
    field: str, value: object, tmp_path: Path
) -> None:
    """Scenario: an optional field that is empty is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="non-empty string"):
        write_record(journal_root, "CR-001", _check_record(**{field: value}))

    assert not journal_root.exists()


def test_an_excerpt_beyond_the_byte_bound_is_refused(tmp_path: Path) -> None:
    """Scenario: an excerpt beyond the byte bound is refused.

    The bound is measured on the field's UTF-8 encoding — 'é' is two
    bytes, so a 2049-character excerpt of them is past 4 KiB while a
    character count would pass.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="at most 4096 UTF-8 bytes"):
        write_record(journal_root, "CR-001", _check_record(excerpt="é" * 2049))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", ("name", "failed_step", "excerpt", "run_url"))
def test_a_displayed_string_that_could_forge_a_line_is_refused(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a displayed string that could forge a line is refused.

    The four fields register under the forgeable-text rule keyed
    `("check", field)` — `commit`'s hex shape and `result`'s vocabulary
    admit no forgeable character, so they carry no registration.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(journal_root, "CR-001", _check_record(**{field: "ok\nforged"}))

    assert not journal_root.exists()


def test_a_check_record_that_names_no_recorder_is_refused() -> None:
    """Scenario: a check record that names no recorder is refused."""

    record = _check_record()
    filename = f"{generate_ulid()}-check.json"
    with pytest.raises(JournalRecordError, match="resolvable recorder"):
        validate_record_content(filename, json.dumps(record))
    record["recorded_by"] = "ci-runner"
    record["recorded_by_source"] = "override"
    assert validate_record_content(filename, json.dumps(record))["recorded_by"] == (
        "ci-runner"
    )


def test_a_check_record_stamps_schema_7() -> None:
    """Scenario: a check record stamps schema 7."""

    record = create_check_record("CR-001", "test", _COMMIT, "unit-tests", "passed")
    assert record["schema"] == 7


def test_a_check_record_stamped_below_7_is_refused_at_write(tmp_path: Path) -> None:
    """Scenario: a check record stamped below 7 is refused at write.

    A check carrying its fields meets the field-admission refusal first,
    as a schema-gated field does; one carrying none of them meets the
    record-type gate. Both are refused before anything is written.
    """

    journal_root = tmp_path / "journal"
    record = _check_record()
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    bare = _check_record()
    bare["schema"] = 6
    for field in ("commit", "name", "result", "failed_step", "excerpt", "run_url"):
        del bare[field]
    with pytest.raises(JournalRecordError, match="require schema 7"):
        write_record(journal_root, "CR-001", bare)

    assert not journal_root.exists()


def test_a_check_record_stamped_below_7_is_refused_on_read(tmp_path: Path) -> None:
    """Scenario: a check record stamped below 7 is refused on read."""

    record = _check_record()
    record["schema"] = 6
    record["recorded_by"] = "ci-runner"
    record["recorded_by_source"] = "override"
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-check.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(tmp_path / "journal", "CR-001")

    bare = {
        "schema": 6,
        "record_type": "check",
        "task": "CR-001",
        "created_at": "2026-10-03T00:00:00Z",
        "tool_version": "test",
        "source": "live",
        "recorded_by": "ci-runner",
        "recorded_by_source": "override",
    }
    bare_dir = tmp_path / "bare-journal" / "tasks" / "CR-001" / "records"
    bare_dir.mkdir(parents=True)
    (bare_dir / f"{generate_ulid()}-check.json").write_text(
        json.dumps(bare), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="require schema 7"):
        read_records(tmp_path / "bare-journal", "CR-001")


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


def test_a_check_record_is_still_accepted_after_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: a check record is still accepted after completion."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _repo, root = _terminal_task(tmp_path, monkeypatch)

    load_task_for_record(root, "CR-001", "check")
    write_record(
        root,
        "CR-001",
        create_check_record(
            "CR-001", "test", _COMMIT, "unit-tests", "failed", failed_step="tests"
        ),
    )

    assert read_records(root, "CR-001")[-1]["record_type"] == "check"
    assert main(["validate"]) == 0


def test_a_check_record_is_still_accepted_after_abandonment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: a check record is still accepted after abandonment."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _repo, root = _terminal_task(tmp_path, monkeypatch, "abandoned")

    load_task_for_record(root, "CR-001", "check")
    write_record(
        root,
        "CR-001",
        create_check_record("CR-001", "test", _COMMIT, "unit-tests", "error"),
    )

    assert read_records(root, "CR-001")[-1]["record_type"] == "check"
    assert main(["validate"]) == 0
