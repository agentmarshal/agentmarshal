"""Tests for the ext record type (ADR-0013 decision 18, ADR-0022 section 3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import run_gate
from agentmarshal.journal.records import (
    JournalRecordError,
    create_abandoned_record,
    create_completed_record,
    create_ext_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.journal.status import TaskStatusError, load_task_for_record
from test_gate import _candidate_head, _commit_all, _gate_repo
from test_journal import initialize_status_repo

_COMMIT = "a" * 40
_KIND = "openspec/change-archived@1"
_PAYLOAD = {"outcome": "archived", "change": "ext-record"}


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    An ext record requires a resolvable recorder, and the ambient
    `AGENTMARSHAL_ACTOR` must not decide whether a test resolves one —
    every test that needs a recorder names the actor itself.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _ext_record(**overrides: Any) -> dict[str, object]:
    record = create_ext_record("CR-001", "test", _KIND, _COMMIT, _PAYLOAD)
    record.update(overrides)
    return record


def _without_recorder(record: dict[str, object]) -> dict[str, object]:
    """Drop the stamped actor pair, so a round-trip compares content only."""

    return {
        key: value
        for key, value in record.items()
        if key not in {"recorded_by", "recorded_by_source"}
    }


def test_an_ext_record_is_written_and_read_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an ext record is written and read back."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert _without_recorder(stored) == record | {"id": stored["id"]}
    assert stored["schema"] == 7
    assert stored["kind"] == _KIND
    assert stored["payload"] == _PAYLOAD
    assert stored["recorded_by"] == "ext-writer"


@pytest.mark.parametrize(
    "kind",
    [
        "openspec",
        "openspec/change-archived",
        "openspec/change-archived@",
        "openspec//change-archived@1",
        "/change-archived@1",
        "openspec/change-archived@1/extra",
        "open spec/change-archived@1",
        "openspec/change-archived@1 ",
        5,
        None,
    ],
)
def test_a_kind_not_of_the_manifests_form_is_refused(
    kind: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a kind not of the manifest's form is refused.

    The rule is the manifest's own — `_RECORD_KIND`, the fullmatch
    `_parse_record_kinds` applies to every `kinds` entry — imported where
    the record rule runs, never copied, so a missing segment, a stray
    separator, whitespace, a non-string and a missing field are all
    refused the same way a manifest would refuse them.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record()
    if kind is None:
        del record["kind"]
    else:
        record["kind"] = kind
    with pytest.raises(JournalRecordError, match=r"'kind'.*<name>/<kind>@<version>"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("kind", ["a/b@c\x07", "a/b@c\u202e"])
def test_a_kind_that_could_forge_a_rendered_line_is_refused(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a kind that could forge a rendered line is refused.

    `kind` registers under the forgeable-text rule keyed `("ext",
    "kind")`, the same guard the manifest's own kind check applies: the
    form rule refuses `@`, `/` and whitespace, but a control character
    or a bidirectional mark is none of those, so the forgeable-text
    entry is what stands behind the form.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(journal_root, "CR-001", _ext_record(kind=kind))

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "commit",
    ["a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + " ", 40, None],
)
def test_a_commit_that_is_not_40_lowercase_hex_is_refused(
    commit: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a commit that is not 40 lowercase hex is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record(commit=commit) if commit is not None else _ext_record()
    if commit is None:
        del record["commit"]
    with pytest.raises(JournalRecordError, match=r"'commit'.*40 .*lowercase hex"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_an_ext_record_that_carries_no_payload_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an ext record that carries no payload is refused.

    `payload` may be any JSON value — `null` among them — so the record
    owes the field itself: presence is checked, never truthiness. A
    `null` payload carries the sha256 of `null` and round-trips.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record()
    del record["payload"]
    with pytest.raises(JournalRecordError, match="must carry 'payload'"):
        write_record(journal_root, "CR-001", record)

    write_record(
        journal_root,
        "CR-001",
        create_ext_record("CR-001", "test", _KIND, _COMMIT, None),
    )
    stored = read_records(journal_root, "CR-001")[0]
    assert stored["payload"] is None
    assert stored["payload_sha256"] == (
        "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b"
    )


def test_a_payload_at_the_byte_bound_is_admitted_and_one_past_it_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario:
    a payload at the byte bound is admitted and one past it is refused.

    The bound is measured on the canonical form — a string payload
    serializes as itself between quotes, so 65534 characters are exactly
    64 KiB and 65535 are one byte over.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    write_record(
        journal_root,
        "CR-001",
        create_ext_record("CR-001", "test", _KIND, _COMMIT, "x" * 65534),
    )
    assert read_records(journal_root, "CR-001")[0]["payload"] == "x" * 65534

    with pytest.raises(JournalRecordError, match=r"'payload'.*at most 65536 bytes"):
        write_record(
            journal_root,
            "CR-001",
            create_ext_record("CR-001", "test", _KIND, _COMMIT, "x" * 65535),
        )


@pytest.mark.parametrize("payload", [float("nan"), float("inf"), -float("inf"), {1, 2}])
def test_a_payload_that_has_no_json_form_is_refused(
    payload: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a payload that has no JSON form is refused.

    The builder computes the pin over the canonical form, so a payload
    with no JSON form — a non-finite number, a value JSON cannot encode
    — is refused there naming `payload`; a hand-carried record meets
    the record rule's same refusal, ahead of the hash check.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="'payload' must be a JSON value"):
        create_ext_record("CR-001", "test", _KIND, _COMMIT, payload)

    record = _ext_record(payload_sha256="0" * 64)
    record["payload"] = payload
    with pytest.raises(JournalRecordError, match="'payload' must be a JSON value"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "sha256",
    ["a" * 63, "a" * 65, "A" * 64, "g" * 64, "a" * 64 + " ", 64, None],
)
def test_a_payload_hash_that_is_not_64_lowercase_hex_is_refused(
    sha256: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a payload hash that is not 64 lowercase hex is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record(payload_sha256=sha256) if sha256 is not None else _ext_record()
    if sha256 is None:
        del record["payload_sha256"]
    with pytest.raises(
        JournalRecordError, match=r"'payload_sha256'.*64 .*lowercase hex"
    ):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_a_payload_hash_that_does_not_match_the_payload_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a payload hash that does not match the payload is refused.

    The pin is over the canonical form — the hash the builder computed
    is replaced by a well-formed 64-hex digest of something else, at
    write and again on read of a file carrying the same lie.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record(payload_sha256="0" * 64)
    with pytest.raises(JournalRecordError, match="canonical form"):
        write_record(journal_root, "CR-001", record)

    record["recorded_by"] = "ext-writer"
    record["recorded_by_source"] = "override"
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-ext.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="canonical form"):
        read_records(journal_root, "CR-001")


def test_the_same_payload_under_another_key_order_hashes_the_same() -> None:
    """Scenario: the same payload under another key order hashes the same.

    The pin is over the canonical form — sorted keys — so a payload
    built with its keys in another order produces the same
    `payload_sha256`, however the record happened to carry them.
    """

    first = create_ext_record(
        "CR-001", "test", _KIND, _COMMIT, {"b": 1, "a": {"y": None, "x": True}}
    )
    second = create_ext_record(
        "CR-001", "test", _KIND, _COMMIT, {"a": {"x": True, "y": None}, "b": 1}
    )
    assert first["payload_sha256"] == second["payload_sha256"]


def test_an_ext_record_that_names_no_recorder_is_refused() -> None:
    """Scenario: an ext record that names no recorder is refused."""

    record = _ext_record()
    filename = f"{generate_ulid()}-ext.json"
    with pytest.raises(JournalRecordError, match="resolvable recorder"):
        validate_record_content(filename, json.dumps(record))
    record["recorded_by"] = "ext-writer"
    record["recorded_by_source"] = "override"
    assert validate_record_content(filename, json.dumps(record))["recorded_by"] == (
        "ext-writer"
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
    write_record(journal_root, "CR-001", _ext_record())

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["recorded_by"] == "an-undeclared-actor"
    assert stored["recorded_by_source"] == "override"


def test_a_candidate_adding_an_ext_record_is_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a candidate adding an ext record is admitted.

    A real repository, the way test_gate's candidate tests build one: the
    task opens and merges, and a candidate branch appends an ext record —
    a journal-only transaction, the lane an appended record takes. The
    gate's record checks pass for it the way they pass for the other
    schema-7 record types the projection admits before a terminal record.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"

    def add_ext() -> None:
        write_record(journal, "CR-001", _ext_record())

    head = _candidate_head(repo, "ext", base, add_ext)

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert "PASS: added records are valid" in output
    assert "PASS: task lifecycle records are consistent" in output


@pytest.mark.parametrize(
    "terminal,state", [("completed", "done"), ("abandoned", "abandoned")]
)
def test_a_candidate_adding_an_ext_record_after_a_terminal_record_is_refused(
    terminal: str, state: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an ext record on a closed task is refused — at the gate.

    The projection's answer the writer-side guard refuses on is the gate's
    own: a candidate that appends an ext record to a task already terminal
    at base is refused, the report naming the projected state — an ext
    record is admitted after a terminal record never, where a measurement
    or a reopening still may be.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_completed_record("CR-001", "test", base)
        if terminal == "completed"
        else create_abandoned_record("CR-001", "test", "Superseded"),
    )
    base = _commit_all(repo, f"close CR-001 ({terminal})")

    def add_ext() -> None:
        write_record(journal, "CR-001", _ext_record())

    head = _candidate_head(repo, "ext-after-terminal", base, add_ext)

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert not report.passed
    assert (
        f"FAIL: task CR-001 is already closed at base (candidate state: {state})"
        in output
    )


def test_status_and_validate_handle_a_task_carrying_an_ext_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status and validate handle a task carrying an ext record."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    repo = tmp_path / "repo"
    root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    write_record(root, "CR-001", _ext_record())

    capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    output = capsys.readouterr().out
    assert "ext" in output
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
def test_an_ext_record_on_a_closed_task_is_refused(
    terminal: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an ext record on a closed task is refused."""

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    root = _terminal_task(tmp_path, monkeypatch, terminal)

    with pytest.raises(TaskStatusError, match="is not open"):
        load_task_for_record(root, "CR-001", "ext")

    assert main(["validate"]) == 0


def test_an_ext_record_stamps_schema_7() -> None:
    """Scenario: an ext record stamps schema 7."""

    record = create_ext_record("CR-001", "test", _KIND, _COMMIT, _PAYLOAD)
    assert record["schema"] == 7


def test_an_ext_record_stamped_below_7_is_refused_at_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an ext record stamped below 7 is refused at write.

    An ext record carrying its fields meets the field-admission refusal
    first, as a schema-gated field does; one carrying none of the family
    meets the record-type gate. Both are refused before anything is
    written.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal_root = tmp_path / "journal"
    record = _ext_record()
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    bare = _ext_record()
    bare["schema"] = 6
    for field in ("kind", "commit", "payload", "payload_sha256"):
        del bare[field]
    with pytest.raises(JournalRecordError, match="require schema 7"):
        write_record(journal_root, "CR-001", bare)

    assert not journal_root.exists()


def test_an_ext_record_stamped_below_7_is_refused_on_read(tmp_path: Path) -> None:
    """Scenario: an ext record stamped below 7 is refused on read."""

    record = _ext_record()
    record["schema"] = 6
    record["recorded_by"] = "ext-writer"
    record["recorded_by_source"] = "override"
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-ext.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(tmp_path / "journal", "CR-001")

    bare = {
        "schema": 6,
        "record_type": "ext",
        "task": "CR-001",
        "created_at": "2026-10-04T00:00:00Z",
        "tool_version": "test",
        "source": "live",
        "recorded_by": "ext-writer",
        "recorded_by_source": "override",
    }
    bare_dir = tmp_path / "bare-journal" / "tasks" / "CR-001" / "records"
    bare_dir.mkdir(parents=True)
    (bare_dir / f"{generate_ulid()}-ext.json").write_text(
        json.dumps(bare), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="require schema 7"):
        read_records(tmp_path / "bare-journal", "CR-001")
