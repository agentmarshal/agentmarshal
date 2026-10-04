"""Tests for the agreement record type (ADR-0018 decision 2, ADR-0022 section 3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_agreement_record,
    create_completed_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from test_journal import initialize_status_repo

_COMMIT = "a" * 40
_HASH = "b" * 64


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    An agreement record requires a resolvable recorder, and the ambient
    `AGENTMARSHAL_ACTOR` must not decide whether a test resolves one —
    every test that needs a recorder names the actor itself.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _agreement_record(**overrides: Any) -> dict[str, object]:
    record = create_agreement_record("CR-001", "test", _HASH)
    record.update(overrides)
    return record


def _without_recorder(record: dict[str, object]) -> dict[str, object]:
    """Drop the stamped actor pair, so a round-trip compares content only."""

    return {
        key: value
        for key, value in record.items()
        if key not in {"recorded_by", "recorded_by_source"}
    }


def test_an_agreement_record_is_written_and_read_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an agreement record is written and read back."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _agreement_record()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert _without_recorder(stored) == record | {"id": stored["id"]}
    assert stored["schema"] == 7
    assert stored["contract"] == _HASH
    assert stored["recorded_by"] == "an-operator"


@pytest.mark.parametrize(
    "contract", ["a" * 63, "a" * 65, "A" * 64, "g" * 64, "a" * 64 + " ", 64]
)
def test_a_contract_hash_that_is_not_64_lowercase_hex_is_refused(
    contract: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a contract hash that is not 64 lowercase hex is refused.

    The shape rule is the contract family's own — `contract-hash-7`, the
    one `opened` and `amendment` answer to — so an upper-case hex string,
    a hash one character short or long, and a non-string are all refused
    by it, ahead of the family's rule.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"64 .*lowercase hex"):
        write_record(journal_root, "CR-001", _agreement_record(contract=contract))

    assert not journal_root.exists()


def test_an_agreement_record_that_carries_no_contract_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an agreement record that carries no contract is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _agreement_record()
    del record["contract"]
    with pytest.raises(JournalRecordError, match="must carry 'contract'"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_a_contract_that_could_forge_a_rendered_line_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a contract that could forge a rendered line is refused.

    `contract` registers under the forgeable-text rule keyed
    `("agreement", "contract")`; its entry never fires, the 64-hex shape
    rule refusing the forgeable character first.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"control characters|lowercase hex"):
        write_record(journal_root, "CR-001", _agreement_record(contract="ok\nforged"))

    assert not journal_root.exists()


def test_an_agreement_record_that_names_no_recorder_is_refused() -> None:
    """Scenario: an agreement record that names no recorder is refused."""

    record = _agreement_record()
    filename = f"{generate_ulid()}-agreement.json"
    with pytest.raises(JournalRecordError, match="resolvable recorder"):
        validate_record_content(filename, json.dumps(record))
    record["recorded_by"] = "an-operator"
    record["recorded_by_source"] = "override"
    assert validate_record_content(filename, json.dumps(record))["recorded_by"] == (
        "an-operator"
    )


def test_a_recorder_that_is_not_a_declared_actor_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a recorder that is not a declared actor is accepted.

    The project's actors table declares no actor at all here, and the
    override names one all the same — the record stands, `recorded_by`
    carrying the name as given, as on `finding` and `check`.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-undeclared-actor")
    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _agreement_record())

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["recorded_by"] == "an-undeclared-actor"
    assert stored["recorded_by_source"] == "override"


def test_a_candidate_adding_an_agreement_record_is_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a candidate adding an agreement record is admitted.

    The gate runs `validate_record_content` over the records a candidate
    adds and asks the projection what a closed task still admits — an
    agreement passes the content check and answers the projection like
    every record type that is not a measurement or a reopening.
    """

    record = _agreement_record(recorded_by="an-operator", recorded_by_source="override")
    filename = f"{generate_ulid()}-agreement.json"
    assert validate_record_content(filename, json.dumps(record))["contract"] == _HASH

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    task = load_task_for_record(root, "CR-001", "agreement")
    assert task.state == "open"


def test_status_and_validate_handle_a_task_carrying_an_agreement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status and validate handle a task carrying an agreement
    record."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    write_record(root, "CR-001", _agreement_record())

    capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    output = capsys.readouterr().out
    assert "agreement" in output
    assert main(["validate"]) == 0


def _terminal_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_type: str = "completed",
) -> Path:
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    if record_type == "completed":
        record = create_completed_record("CR-001", "test", _COMMIT)
    else:
        record = create_abandoned_record("CR-001", "test", "Superseded")
    write_record(root, "CR-001", record)
    return root


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_an_agreement_on_a_closed_task_is_refused(
    terminal: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an agreement on a closed task is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    root = _terminal_task(tmp_path, monkeypatch, terminal)

    with pytest.raises(TaskStatusError, match="is not open"):
        load_task_for_record(root, "CR-001", "agreement")

    assert main(["validate"]) == 0


def test_an_agreement_record_stamps_schema_7() -> None:
    """Scenario: an agreement record stamps schema 7."""

    record = create_agreement_record("CR-001", "test", _HASH)
    assert record["schema"] == 7


def test_an_agreement_record_stamped_below_7_is_refused_at_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an agreement record stamped below 7 is refused at write.

    An agreement carrying `contract` meets the field-admission refusal
    first, as a schema-gated field does; one carrying none of the family
    meets the record-type gate. Both are refused before anything is
    written.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    journal_root = tmp_path / "journal"
    record = _agreement_record()
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    bare = _agreement_record()
    bare["schema"] = 6
    del bare["contract"]
    with pytest.raises(JournalRecordError, match="require schema 7"):
        write_record(journal_root, "CR-001", bare)

    assert not journal_root.exists()


def test_an_agreement_record_stamped_below_7_is_refused_on_read(
    tmp_path: Path,
) -> None:
    """Scenario: an agreement record stamped below 7 is refused on read."""

    record = _agreement_record()
    record["schema"] = 6
    record["recorded_by"] = "an-operator"
    record["recorded_by_source"] = "override"
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-agreement.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(tmp_path / "journal", "CR-001")

    bare = {
        "schema": 6,
        "record_type": "agreement",
        "task": "CR-001",
        "created_at": "2026-10-04T00:00:00Z",
        "tool_version": "test",
        "source": "live",
        "recorded_by": "an-operator",
        "recorded_by_source": "override",
    }
    bare_dir = tmp_path / "bare-journal" / "tasks" / "CR-001" / "records"
    bare_dir.mkdir(parents=True)
    (bare_dir / f"{generate_ulid()}-agreement.json").write_text(
        json.dumps(bare), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="require schema 7"):
        read_records(tmp_path / "bare-journal", "CR-001")
