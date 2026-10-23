"""Tests for the review record's link, classes and actor fields (ADR-0022 s2).

`previous_review` and `classes` are top-level fields of the schema-7
review family (ADR-0016 decisions 2 and 3); `actor` is a key of the
`reviewer` object (ADR-0018 decision 3), admitted by the record's own
schema. The second half exercises the launcher writing the first two —
the link read before the reviewer runs, and the classes normalized
against the project's vocabulary.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import records as records_module
from agentmarshal.journal import review
from agentmarshal.journal.records import (
    JournalRecordError,
    create_review_record,
    generate_ulid,
    read_records,
    validate_record_content,
    write_record,
)
from agentmarshal.settings import DEFAULT_FINDING_CLASSES
from test_review_launcher import (
    _finding_args,
    _finding_verdict,
    _record_finding,
    _review_repo,
    _reviewer_stub,
    _run_review,
    _verdict,
)

_COMMIT = "a" * 40
_REVIEWER = ("qa", "vendor", "model", "r@x.i")
_FINDING_1 = "01J00000000000000000000001"
_FINDING_2 = "01J00000000000000000000002"
_ADVISORY = "01J0000000000000000000000A"
_PREVIOUS = "01J00000000000000000000000"


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
        previous_review=_PREVIOUS,
        classes={_FINDING_1: "correctness", _ADVISORY: "style"},
        reviewer_actor="claude",
    )
    record.update(overrides)
    return record


def _with_actor(record: dict[str, object], actor: object) -> dict[str, object]:
    cast(dict[str, object], record["reviewer"])["actor"] = actor
    return record


def _plain_review() -> dict[str, object]:
    """A review record carrying none of the family's fields."""

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


_FAMILY_FIELDS = ("previous_review", "classes", "reviewer.actor")


def _carrying(record: dict[str, object], field: str) -> dict[str, object]:
    """Add one field of the family to a plain review record."""

    if field == "previous_review":
        record["previous_review"] = _PREVIOUS
    elif field == "classes":
        record["classes"] = {_FINDING_1: "correctness"}
    else:
        _with_actor(record, "claude")
    return record


def test_a_review_carrying_previous_review_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a review carrying previous_review is written and read back."""

    journal_root = tmp_path / "journal"
    record = create_review_record(
        "CR-001",
        "test",
        _COMMIT,
        "changes_required",
        *_REVIEWER,
        [_FINDING_1],
        previous_review=_PREVIOUS,
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["previous_review"] == _PREVIOUS
    assert stored["schema"] == 7


@pytest.mark.parametrize(
    "previous",
    [
        "01J0000000000000000000000",  # 25 characters
        "01J0000000000000000000000BB",  # 27 characters
        "01J0000000000000000000000U",  # U is not Crockford base32
        "81J00000000000000000000000",  # the leading digit is 0-7
        "",
        26,
        None,
    ],
)
def test_a_previous_review_that_is_not_a_record_id_is_refused(
    previous: object, tmp_path: Path
) -> None:
    """Scenario: a previous_review that is not a record id is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="previous_review"):
        write_record(journal_root, "CR-001", _review_record(previous_review=previous))

    assert not journal_root.exists()


def test_a_previous_review_that_could_forge_a_line_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: a previous_review that could forge a line is refused.

    The ULID shape admits no forgeable character, so the family's shape
    rule refuses first; `("review", "previous_review")` stays registered
    under the forgeable-text rule behind it, as `commit`'s entries are.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError):
        write_record(
            journal_root,
            "CR-001",
            _review_record(previous_review=f"{_PREVIOUS}\n"),
        )

    assert not journal_root.exists()


def test_a_review_carrying_classes_for_its_findings_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a review carrying classes for its findings is written and
    read back."""

    journal_root = tmp_path / "journal"
    record = create_review_record(
        "CR-001",
        "test",
        _COMMIT,
        "changes_required",
        *_REVIEWER,
        [_FINDING_1, _FINDING_2],
        advisory_findings=[_ADVISORY],
        classes={
            _FINDING_1: "correctness",
            _FINDING_2: "test-gap",
            _ADVISORY: "style",
        },
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["classes"] == {
        _FINDING_1: "correctness",
        _FINDING_2: "test-gap",
        _ADVISORY: "style",
    }
    assert stored["schema"] == 7


def test_a_class_outside_the_projects_vocabulary_is_admitted(
    tmp_path: Path,
) -> None:
    """Scenario: a class outside the project's vocabulary is admitted.

    The record does not know the vocabulary — mapping a foreign class to
    `other` is the writer's, a later task (ADR-0016 decision 3).
    """

    journal_root = tmp_path / "journal"
    record = create_review_record(
        "CR-001",
        "test",
        _COMMIT,
        "changes_required",
        *_REVIEWER,
        [_FINDING_1],
        classes={_FINDING_1: "a-class-the-vocabulary-lacks"},
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["classes"] == {_FINDING_1: "a-class-the-vocabulary-lacks"}


@pytest.mark.parametrize(
    "classes",
    [
        {"01J00000000000000000000009": "correctness"},  # no finding of the record
        {_FINDING_1: "correctness", "F-9": "style"},
    ],
)
def test_a_classes_key_naming_no_finding_of_the_record_is_refused(
    classes: dict[str, str], tmp_path: Path
) -> None:
    """Scenario: a classes key naming no finding of the record is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="classes"):
        write_record(journal_root, "CR-001", _review_record(classes=classes))

    assert not journal_root.exists()


def test_an_empty_classes_object_is_refused(tmp_path: Path) -> None:
    """Scenario: an empty classes object is refused.

    A review with nothing classified carries no `classes`, the way
    `advisory_findings` is omitted when empty — an empty object is a
    second way to say the same thing, refused as a writer's bug.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="classes"):
        write_record(journal_root, "CR-001", _review_record(classes={}))

    assert not journal_root.exists()


@pytest.mark.parametrize("classes", ["correctness", [_FINDING_1], 5])
def test_a_classes_that_is_not_an_object_is_refused(
    classes: object, tmp_path: Path
) -> None:
    """Scenario: a classes that is not an object is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="classes"):
        write_record(journal_root, "CR-001", _review_record(classes=classes))

    assert not journal_root.exists()


@pytest.mark.parametrize("value", ["", "   ", 5, None])
def test_a_class_value_that_is_empty_or_not_a_string_is_refused(
    value: object, tmp_path: Path
) -> None:
    """Scenario: a class value that is empty or not a string is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="classes"):
        write_record(
            journal_root,
            "CR-001",
            _review_record(classes={_FINDING_1: value}),
        )

    assert not journal_root.exists()


def test_a_class_value_that_could_forge_a_line_is_refused(tmp_path: Path) -> None:
    """Scenario: a class value that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(
            journal_root,
            "CR-001",
            _review_record(classes={_FINDING_1: "ok\nforged"}),
        )

    assert not journal_root.exists()


def test_a_review_whose_reviewer_carries_actor_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: a review whose reviewer carries actor is written and
    read back."""

    journal_root = tmp_path / "journal"
    record = create_review_record(
        "CR-001",
        "test",
        _COMMIT,
        "approved",
        *_REVIEWER,
        [],
        reviewer_actor="claude",
    )
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    reviewer = cast(dict[str, object], stored["reviewer"])
    assert reviewer["actor"] == "claude"
    assert stored["schema"] == 7


@pytest.mark.parametrize("actor", ["", "   ", 5, None])
def test_an_actor_that_is_empty_or_not_a_string_is_refused(
    actor: object, tmp_path: Path
) -> None:
    """Scenario: an actor that is empty or not a string is refused."""

    journal_root = tmp_path / "journal"
    record = _with_actor(_review_record(), actor)
    with pytest.raises(JournalRecordError, match="actor"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_an_actor_that_could_forge_a_line_is_refused(tmp_path: Path) -> None:
    """Scenario: an actor that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    record = _with_actor(_review_record(), "claude\nforged")
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_the_reviewer_object_stays_closed_to_any_other_key(tmp_path: Path) -> None:
    """Scenario: the reviewer object stays closed to any other key."""

    journal_root = tmp_path / "journal"
    record = _review_record()
    cast(dict[str, object], record["reviewer"])["token"] = "not-a-reviewer-key"
    with pytest.raises(JournalRecordError, match="must contain only"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("field", _FAMILY_FIELDS)
def test_a_review_carrying_a_field_of_the_family_stamps_schema_7(
    field: str,
) -> None:
    """Scenario: a review carrying a field of the family stamps schema 7."""

    assert records_module._minimum_schema(_carrying(_plain_review(), field)) == 7


@pytest.mark.parametrize("field", _FAMILY_FIELDS)
def test_a_field_of_the_family_on_a_review_below_schema_7_is_refused_at_write(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a field of the family on a review below schema 7 is
    refused at write."""

    journal_root = tmp_path / "journal"
    record = _plain_review()
    record["schema"] = 6
    with pytest.raises(JournalRecordError):
        write_record(journal_root, "CR-001", _carrying(record, field))

    assert not journal_root.exists()


@pytest.mark.parametrize("field", _FAMILY_FIELDS)
def test_a_field_of_the_family_on_a_review_below_schema_7_is_refused_on_read(
    field: str, tmp_path: Path
) -> None:
    """Scenario: a field of the family on a review below schema 7 is
    refused on read.

    The two top-level fields meet the field-admission rule of the
    record's own schema; `reviewer.actor` meets the reviewer object's
    closed keys under that schema — the `review` rule is bound to 1, so
    the read side refuses it too, not only the writer.
    """

    record = _plain_review()
    record["schema"] = 6
    journal_root = _journal_holding(tmp_path, _carrying(record, field))
    with pytest.raises(JournalRecordError):
        read_records(journal_root, "CR-001")


def test_a_review_carrying_none_of_the_fields_keeps_its_schema_and_reads_as_before(
    tmp_path: Path,
) -> None:
    """Scenario: a review carrying none of the fields keeps its schema and
    reads as before."""

    journal_root = tmp_path / "journal"
    record = _plain_review()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["schema"] == 3
    assert "previous_review" not in stored
    assert "classes" not in stored
    assert cast(dict[str, object], stored["reviewer"]).keys() == {
        "role",
        "vendor",
        "model",
        "email",
    }


def test_the_family_is_declared_through_the_schema_7_registrations() -> None:
    """The family registers through the CR-154 mechanism alone: a
    `_FIELD_FAMILIES` entry, a `_FORGEABLE_TEXT_FIELDS` entry for
    `previous_review`, a shape rule bound to 7 and the minimum-schema
    derivation — never a second mechanism."""

    family = records_module._SCHEMA_7_REVIEW_FIELDS
    assert family == {"previous_review", "classes", "verification", "evidence"}
    assert (7, "review", family) in records_module._FIELD_FAMILIES
    assert ("review", "previous_review") in records_module._FORGEABLE_TEXT_FIELDS
    assert records_module._RULE_FROM_SCHEMA["review-fields-7"] == 7


def test_the_gate_path_refuses_a_review_below_7_carrying_a_field() -> None:
    """The gate's own write-side check — `validate_record_content`, run on
    every record a candidate adds — refuses the same records the writer
    does."""

    record = _review_record()
    record["schema"] = 6
    filename = f"{generate_ulid()}-review.json"
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        validate_record_content(filename, json.dumps(record))


@pytest.fixture(autouse=True)
def _isolated_temp_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Give the launcher's kept outputs an isolated temp dir to land in."""

    system_temp = Path(tempfile.gettempdir())
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    return system_temp


def _reviews(repo: Path) -> list[dict[str, object]]:
    """The task's review records in journal order."""

    return [
        record
        for record in read_records(repo / ".agentmarshal" / "journal", "CR-001")
        if record["record_type"] == "review"
    ]


def _verdict_with_classes(
    commit: str,
    verdict: str,
    findings: list[str],
    classes: object,
    advisory_findings: list[str] | None = None,
) -> str:
    """A commit verdict whose ``classes`` may be deliberately malformed."""

    data: dict[str, object] = {
        "reviewed_commit": commit,
        "verdict": verdict,
        "findings": findings,
        "classes": classes,
    }
    if advisory_findings is not None:
        data["advisory_findings"] = advisory_findings
    return f"AGENTMARSHAL_VERDICT_BEGIN\n{json.dumps(data)}\nAGENTMARSHAL_VERDICT_END\n"


def _finding_verdict_with_classes(
    finding: str, verdict: str, findings: list[str], classes: object
) -> str:
    data: dict[str, object] = {
        "reviewed_finding": finding,
        "verdict": verdict,
        "findings": findings,
        "classes": classes,
    }
    return f"AGENTMARSHAL_VERDICT_BEGIN\n{json.dumps(data)}\nAGENTMARSHAL_VERDICT_END\n"


def _submit_review_args() -> list[str]:
    return [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        "b" * 40,
        "--verdict",
        "approved",
        "--role",
        "reviewer",
        "--vendor",
        "human",
        "--model",
        "none",
        "--email",
        "reviewer@test.invalid",
    ]


def test_a_second_launched_review_links_the_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a second launched review links the first."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    assert _run_review(commit) == 0
    stub = _reviewer_stub(tmp_path, _verdict(commit, "changes_required", ["F-1"]))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    first, second = _reviews(repo)
    assert second["previous_review"] == first["id"]
    assert second["schema"] == 7


def test_the_first_launched_review_carries_no_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the first launched review carries no link."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert "previous_review" not in record


def test_a_launched_finding_review_links_the_same_way(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a launched finding review links the same way.

    The earlier review here binds to a commit — the link names whatever
    the latest review bound to.
    """

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    assert _run_review(commit) == 0
    finding = _record_finding(repo, [("evidence/log.txt", b"conclusion\n")])
    stub = _reviewer_stub(
        tmp_path,
        _finding_verdict(finding, "approved", []),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main(_finding_args(finding)) == 0

    first, second = _reviews(repo)
    assert second["reviewed_finding"] == finding
    assert second["previous_review"] == first["id"]


def test_submit_review_writes_no_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: submit-review writes no link."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    assert _run_review(commit) == 0

    assert main(_submit_review_args()) == 0

    _launched, submitted = _reviews(repo)
    assert "previous_review" not in submitted
    assert "classes" not in submitted


def test_the_link_is_the_latest_review_at_launch_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the link names the latest review at launch time.

    A record landing while the reviewer runs is read at record time by
    the writers — but this record's link was fixed at launch, so a
    concurrent review becomes the new review's successor's predecessor,
    never its own.
    """

    repo, commit = _review_repo(tmp_path, monkeypatch)
    journal_root = repo / ".agentmarshal" / "journal"
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    assert _run_review(commit) == 0
    earlier = _reviews(repo)[0]

    real_run_reviewer = review._run_reviewer
    concurrent = create_review_record(
        "CR-001", "test", "b" * 40, "approved", *_REVIEWER, []
    )

    def record_then_run(
        command: list[str], cwd: Path, prompt: str
    ) -> tuple[bytes, bytes]:
        write_record(journal_root, "CR-001", concurrent)
        return real_run_reviewer(command, cwd, prompt)

    monkeypatch.setattr(review, "_run_reviewer", record_then_run)

    assert _run_review(commit) == 0

    _first, concurrent_record, launched = _reviews(repo)
    assert launched["previous_review"] == earlier["id"]
    assert launched["previous_review"] != concurrent_record["id"]
    assert launched["previous_review"] != launched["id"]


def test_the_prompt_lists_the_default_vocabulary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the prompt lists the default vocabulary."""

    _repo, commit = _review_repo(tmp_path, monkeypatch)
    prompt_output = tmp_path / "prompt.txt"
    stub = _reviewer_stub(
        tmp_path,
        _verdict(commit, "approved", []),
        prompt_output=prompt_output,
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    prompt = prompt_output.read_text(encoding="utf-8")
    assert "one class per id" in prompt
    for finding_class in DEFAULT_FINDING_CLASSES:
        assert finding_class in prompt


def test_the_prompt_lists_the_projects_configured_vocabulary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the prompt lists the project's configured vocabulary."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["review"] = {"finding_classes": ["bug", "nit"]}
    project_path.write_text(json.dumps(project), encoding="utf-8")
    prompt_output = tmp_path / "prompt.txt"
    stub = _reviewer_stub(
        tmp_path,
        _verdict(commit, "approved", []),
        prompt_output=prompt_output,
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    prompt = prompt_output.read_text(encoding="utf-8")
    assert "bug, nit" in prompt
    assert "correctness" not in prompt


def test_a_classes_object_is_admitted_by_the_protocol() -> None:
    """Scenario: a classes object is admitted by the protocol."""

    output = _verdict_with_classes(
        "a" * 40, "changes_required", ["F-1"], {"F-1": "correctness"}
    )

    parsed = review._parse_verdict(output, preserve_output=False)

    assert parsed[5] == {"F-1": "correctness"}


def test_classes_for_the_verdicts_ids_are_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: classes for the verdict's ids are recorded."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(
            commit,
            "changes_required",
            ["F-1"],
            {"F-1": "correctness", "A-1": "style"},
            advisory_findings=["A-1"],
        ),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert record["classes"] == {"F-1": "correctness", "A-1": "style"}
    assert record["schema"] == 7
    assert "note:" not in capsys.readouterr().err


def test_classes_for_the_verdicts_ids_are_recorded_on_a_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: classes for the verdict's ids are recorded — the
    finding-binding form."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    finding = _record_finding(repo, [("evidence/log.txt", b"conclusion\n")])
    stub = _reviewer_stub(
        tmp_path,
        _finding_verdict_with_classes(
            finding, "changes_required", ["F-1"], {"F-1": "security"}
        ),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main(_finding_args(finding)) == 0

    (record,) = _reviews(repo)
    assert record["classes"] == {"F-1": "security"}


def test_a_class_outside_the_vocabulary_records_as_other_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a class outside the vocabulary records as other with a
    warning."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(
            commit, "changes_required", ["F-1"], {"F-1": "bogus-class"}
        ),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert record["classes"] == {"F-1": "other"}
    captured = capsys.readouterr()
    assert "F-1" in captured.err
    assert "bogus-class" in captured.err
    assert "other" in captured.err
    # The warning rides the diagnostics channel; stdout stays the record path.
    assert captured.out.strip().endswith(".json")


def test_an_entry_for_an_id_the_verdict_does_not_carry_is_dropped_with_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an entry for an id the verdict does not carry is dropped
    with a warning."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(
            commit,
            "changes_required",
            ["F-1"],
            {"F-1": "correctness", "G-9": "style"},
        ),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert record["classes"] == {"F-1": "correctness"}
    captured = capsys.readouterr()
    assert "G-9" in captured.err
    assert "style" in captured.err


def test_a_classes_naming_only_unnamed_ids_lands_no_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an entry for an id the verdict does not carry is dropped
    with a warning — none kept means no ``classes`` field at all."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(commit, "changes_required", ["F-1"], {"G-9": "style"}),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert "classes" not in record
    assert "G-9" in capsys.readouterr().err


@pytest.mark.parametrize("classes", ["correctness", ["F-1"], 5, None])
def test_a_classes_that_is_not_an_object_is_dropped_whole_with_a_warning(
    classes: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a classes that is not an object is dropped whole with a
    warning — the paid verdict is still recorded."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(commit, "changes_required", ["F-1"], classes),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert "classes" not in record
    assert "is not an object" in capsys.readouterr().err


@pytest.mark.parametrize("value", [5, " ", "ok\nforged"])
def test_a_classes_holding_a_value_that_is_no_class_string_is_dropped_whole(
    value: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a classes holding a value that is no class string is
    dropped whole — the verdict is never refused over a class."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(
            commit,
            "changes_required",
            ["F-1"],
            {"F-1": "correctness", "F-2": value},
        ),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert "classes" not in record
    assert "not a usable class string" in capsys.readouterr().err


def test_a_verdict_without_classes_records_exactly_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a verdict without classes records exactly as before —
    no ``classes`` field, the schema stamp rising only for
    ``previous_review``."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    assert _run_review(commit) == 0
    stub = _reviewer_stub(tmp_path, _verdict(commit, "changes_required", ["F-1"]))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    first, second = _reviews(repo)
    assert "classes" not in first
    assert "classes" not in second
    assert second["previous_review"] == first["id"]
    assert second["schema"] == 7


def test_an_empty_classes_object_warns_and_records_no_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty `classes` object is a present-but-empty markup — dropped
    with a note, the way the dropped-whole scenarios read."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path,
        _verdict_with_classes(commit, "changes_required", ["F-1"], {}),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    (record,) = _reviews(repo)
    assert "classes" not in record
    assert "empty object" in capsys.readouterr().err
