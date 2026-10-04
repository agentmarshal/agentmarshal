"""Tests for the pause and operational acceptance forms (ADR-0013, ADR-0022)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import gate as gate_module
from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.gate import run_findings_gate, run_gate
from agentmarshal.journal.records import (
    JournalRecordError,
    create_acceptance_record,
    generate_ulid,
    read_records,
    write_record,
)
from agentmarshal.journal.status import TaskStatus
from test_gate import _gate_repo, _implement, _require_changes
from test_journal import initialize_status_repo

_COMMIT = "a" * 40
_FINDING_ID = "01J00000000000000000000000"


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _pause_record(**overrides: Any) -> dict[str, object]:
    record = create_acceptance_record(
        "CR-001",
        "test",
        _COMMIT,
        "operator@example.invalid",
        None,
        "The pause is understood",
        accepted_pause="openspec",
    )
    record.update(overrides)
    return record


def _operational_record(**overrides: Any) -> dict[str, object]:
    record = create_acceptance_record(
        "CR-001",
        "test",
        _COMMIT,
        "operator@example.invalid",
        None,
        "Switching the extension off is operational",
        operational=True,
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


def test_an_acceptance_of_an_extension_pause_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: an acceptance of an extension pause is written and read back."""

    journal_root = tmp_path / "journal"
    record = _pause_record()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert _without_recorder(stored) == record | {"id": stored["id"]}
    assert stored["accepted_pause"] == {"extension": "openspec"}
    assert "findings" not in stored


def test_an_acceptance_of_an_operational_cr_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Scenario: an acceptance of an operational CR is written and read back."""

    journal_root = tmp_path / "journal"
    record = _operational_record()
    write_record(journal_root, "CR-001", record)

    stored = read_records(journal_root, "CR-001")[0]
    assert _without_recorder(stored) == record | {"id": stored["id"]}
    assert stored["operational"] is True
    assert "findings" not in stored


@pytest.mark.parametrize(
    "accepted_pause",
    [
        "openspec",
        ["openspec"],
        {},
        {"extension": "openspec", "stage": "pre-gate-stop"},
        {"name": "openspec"},
    ],
)
def test_an_accepted_pause_that_is_not_exactly_an_extension_object_is_refused(
    accepted_pause: object, tmp_path: Path
) -> None:
    """Scenario: an accepted_pause that is not exactly an extension object is
    refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="carrying only 'extension'"):
        write_record(
            journal_root, "CR-001", _pause_record(accepted_pause=accepted_pause)
        )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "extension",
    ["", ".", "..", "a/b", "a\\b", "a/b/c", 5, None],
)
def test_an_extension_name_that_is_not_one_non_empty_path_component_is_refused(
    extension: object, tmp_path: Path
) -> None:
    """Scenario: an extension name that is not one non-empty path component is
    refused.

    The rule is the one extension manifests apply to a name — `_validate_name`
    in extensions.py: not empty, never `.` or `..`, carrying no `/` or `\\`.
    """

    journal_root = tmp_path / "journal"
    record = _pause_record(accepted_pause={"extension": extension})
    match = (
        "must be a string"
        if not isinstance(extension, str)
        else ("one non-empty path component")
    )
    with pytest.raises(JournalRecordError, match=match):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("extension", ["ok\nforged", "reorder\u202ex"])
def test_an_extension_name_that_could_forge_a_line_is_refused(
    extension: str, tmp_path: Path
) -> None:
    """Scenario: an extension name that could forge a line is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="control characters"):
        write_record(
            journal_root,
            "CR-001",
            _pause_record(accepted_pause={"extension": extension}),
        )

    assert not journal_root.exists()


def test_a_pause_acceptance_bound_to_a_finding_is_refused(tmp_path: Path) -> None:
    """Scenario: a pause acceptance bound to a finding is refused."""

    journal_root = tmp_path / "journal"
    record = _pause_record()
    del record["accepted_commit"]
    record["accepted_finding"] = _FINDING_ID
    with pytest.raises(JournalRecordError, match="never 'accepted_finding'"):
        write_record(journal_root, "CR-001", record)
    with pytest.raises(JournalRecordError, match="never 'accepted_finding'"):
        create_acceptance_record(
            "CR-001",
            "test",
            None,
            "op",
            None,
            "r",
            accepted_finding=_FINDING_ID,
            accepted_pause="openspec",
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("operational", [False, "true", 1, 0, None])
def test_an_operational_value_other_than_true_is_refused(
    operational: object, tmp_path: Path
) -> None:
    """Scenario: an operational value other than true is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match="'operational' must be true"):
        write_record(
            journal_root, "CR-001", _operational_record(operational=operational)
        )

    assert not journal_root.exists()


def test_an_operational_acceptance_bound_to_a_finding_is_refused(
    tmp_path: Path,
) -> None:
    """Scenario: an operational acceptance bound to a finding is refused."""

    journal_root = tmp_path / "journal"
    record = _operational_record()
    del record["accepted_commit"]
    record["accepted_finding"] = _FINDING_ID
    with pytest.raises(JournalRecordError, match="never 'accepted_finding'"):
        write_record(journal_root, "CR-001", record)
    with pytest.raises(JournalRecordError, match="never 'accepted_finding'"):
        create_acceptance_record(
            "CR-001",
            "test",
            None,
            "op",
            None,
            "r",
            accepted_finding=_FINDING_ID,
            operational=True,
        )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "extra",
    [
        {"findings": ["F-1"], "accepted_pause": {"extension": "openspec"}},
        {"accepted_pause": {"extension": "openspec"}, "operational": True},
        {"findings": ["F-1"], "operational": True},
        {
            "findings": ["F-1"],
            "accepted_pause": {"extension": "openspec"},
            "operational": True,
        },
        {},
    ],
)
def test_a_record_carrying_more_or_fewer_than_exactly_one_form_is_refused(
    extra: dict[str, object], tmp_path: Path
) -> None:
    """Scenario: a record carrying more or fewer than exactly one form is
    refused."""

    journal_root = tmp_path / "journal"
    record = _pause_record()
    del record["accepted_pause"]
    record.update(extra)
    with pytest.raises(
        JournalRecordError,
        match="exactly one of 'findings', 'accepted_pause' or 'operational'",
    ):
        write_record(journal_root, "CR-001", record)
    if not extra:
        with pytest.raises(JournalRecordError, match="exactly one of"):
            create_acceptance_record("CR-001", "test", _COMMIT, "op", None, "r")
        with pytest.raises(JournalRecordError, match="exactly one of"):
            create_acceptance_record(
                "CR-001",
                "test",
                _COMMIT,
                "op",
                ["F-1"],
                "r",
                accepted_pause="openspec",
            )

    assert not journal_root.exists()


@pytest.mark.parametrize(
    "findings",
    [[], "F-1", ["F-1", "F-1"], ["F-1", ""], ["F-1\nforged"]],
)
def test_an_acceptance_over_findings_keeps_its_validation(
    findings: object, tmp_path: Path
) -> None:
    """Scenario: an acceptance over findings keeps its validation."""

    journal_root = tmp_path / "journal"
    record = _pause_record()
    del record["accepted_pause"]
    record["findings"] = findings
    with pytest.raises(JournalRecordError):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


def test_a_writer_stamps_7_for_an_acceptance_carrying_a_new_form() -> None:
    """Scenario: a writer stamps 7 for an acceptance carrying a new form."""

    assert _pause_record()["schema"] == 7
    assert _operational_record()["schema"] == 7


@pytest.mark.parametrize("form", ["accepted_pause", "operational"])
@pytest.mark.parametrize("schema", [3, 6])
def test_an_acceptance_carrying_a_new_form_below_schema_7_is_refused_at_write(
    form: str, schema: int, tmp_path: Path
) -> None:
    """Scenario: an acceptance carrying a new form below schema 7 is refused at
    write."""

    journal_root = tmp_path / "journal"
    record = _pause_record() if form == "accepted_pause" else _operational_record()
    record["schema"] = schema
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("form", ["accepted_pause", "operational"])
def test_an_acceptance_carrying_a_new_form_below_schema_7_is_refused_on_read(
    form: str, tmp_path: Path
) -> None:
    """Scenario: an acceptance carrying a new form below schema 7 is refused on
    read."""

    record = _pause_record() if form == "accepted_pause" else _operational_record()
    record["schema"] = 6
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / f"{generate_ulid()}-acceptance.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(tmp_path / "journal", "CR-001")


def test_an_acceptance_over_findings_keeps_its_stamp() -> None:
    """Scenario: an acceptance over findings keeps its stamp."""

    assert (
        create_acceptance_record("CR-001", "test", _COMMIT, "op", ["F-1"], "r")[
            "schema"
        ]
        == 3
    )
    assert (
        create_acceptance_record(
            "CR-001",
            "test",
            None,
            "op",
            ["F-1"],
            "r",
            accepted_finding=_FINDING_ID,
        )["schema"]
        == 4
    )


# --- the readers -----------------------------------------------------------


def test_a_pause_acceptance_does_not_shadow_an_acceptance_over_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a pause acceptance does not shadow an acceptance over
    findings.

    The commit binding is the lane where a later record could hide the one
    the gate must judge: the findings acceptance stands first, a pause
    acceptance of the same commit is written after it, and the gate still
    judges the findings acceptance.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            head,
            "operator@example.invalid",
            ["F-001"],
            "Accepted over the findings",
        ),
    )
    write_record(journal, "CR-001", _pause_record(accepted_commit=head))
    write_record(journal, "CR-001", _operational_record(accepted_commit=head))

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert (
        "PASS: accepted over findings F-001 by operator@example.invalid; "
        "not an approving review" in output
    )


def test_the_findings_lane_judges_only_an_acceptance_carrying_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a pause acceptance does not shadow an acceptance over
    findings — on the finding binding.

    The records are handed to the gate in memory, the shape a writer around
    the writer could land: an operational acceptance bound to the finding
    after a covering findings acceptance. Without the field's presence as
    the judgment's filter the lane would take the newer record and read
    `findings` off it.
    """

    repo = tmp_path / "repo"
    journal_root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    task = TaskStatus(
        task_id="CR-001",
        contract=ContractHeader(
            schema=1, id="CR-001", title="Task", scope=(), acceptance=()
        ),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            {
                "id": "r-finding",
                "record_type": "finding",
                "created_at": "t1",
                "summary": "a finding",
                "artifacts": [{"ref": "missing.md", "hash": "0" * 64}],
            },
            {
                "id": "r-review",
                "record_type": "review",
                "created_at": "t2",
                "reviewed_finding": "r-finding",
                "verdict": "changes_required",
                "findings": ["F-1"],
                "reviewer": {
                    "role": "qa",
                    "vendor": "v",
                    "model": "m",
                    "email": "outsider@test.invalid",
                },
            },
            {
                "id": "r-acceptance",
                "record_type": "acceptance",
                "created_at": "t3",
                "accepted_finding": "r-finding",
                "accepted_by": "op",
                "findings": ["F-1"],
                "reason": "accepted",
            },
            {
                "id": "r-operational",
                "record_type": "acceptance",
                "created_at": "t4",
                "accepted_finding": "r-finding",
                "accepted_by": "op",
                "operational": True,
                "reason": "not an acceptance over findings",
            },
        ),
        state="open",
    )
    monkeypatch.setattr(gate_module, "load_task_status", lambda *_args, **_keys: task)

    report = run_findings_gate(journal_root, "CR-001")

    assert (
        "PASS: accepted over findings F-1 by op; not an approving review"
        in report.lines
    )


def test_an_acceptance_without_findings_is_not_judged_as_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acceptance without findings is not judged as one.

    A pause acceptance bound to the candidate is no acceptance over
    findings: standing alone it satisfies nothing, and written after a
    mismatched findings acceptance it rescues nothing.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", _pause_record(accepted_commit=head))

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert not report.passed
    assert "accepted over findings" not in output
    assert f"FAIL: latest review of {head[:12]} is approved" in output

    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            head,
            "operator@example.invalid",
            ["F-002"],
            "A mismatched acceptance",
        ),
    )

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert not report.passed
    assert "accepted over findings" not in output
    assert f"FAIL: acceptance of {head[:12]} does not cover the latest" in output


def _status_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, str]:
    """A repo with an opened task and one committed file to accept."""

    repo = tmp_path / "repo"
    journal_root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    (repo / "tracked.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "tracked",
        ],
        cwd=repo,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return repo, journal_root, commit


def test_status_prints_a_pause_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status prints a pause acceptance.

    The record line names `accepted_pause=<extension>` where an acceptance
    over findings names its findings; the summary names the accepted pause,
    and the self-acceptance marking applies the way it does to an
    `accepted_commit` acceptance.
    """

    _repo, journal, commit = _status_repo(tmp_path, monkeypatch)
    write_record(
        journal,
        "CR-001",
        _pause_record(accepted_commit=commit, accepted_by="test@example.invalid"),
    )

    assert main(["status", "CR-001"]) == 0

    output = capsys.readouterr().out
    assert (
        "Acceptance: accepted pause of extension openspec by "
        "test@example.invalid (self-accepted: accepting party is a declared "
        "author or committer)" in output
    )
    (record_line,) = (line for line in output.splitlines() if " acceptance " in line)
    assert record_line.endswith(
        f"accepted_commit={commit[:7]} accepted_by=test@example.invalid "
        "accepted_pause=openspec reason=The pause is understood self-accepted"
    )
    assert "findings=" not in record_line


def test_status_marks_a_pause_acceptance_it_cannot_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status prints a pause acceptance — unchecked.

    A commit the checkout cannot read carries the same unchecked marking an
    `accepted_commit` acceptance over findings carries.
    """

    _repo, journal, _commit = _status_repo(tmp_path, monkeypatch)
    write_record(journal, "CR-001", _pause_record())

    assert main(["status", "CR-001"]) == 0

    output = capsys.readouterr().out
    assert "accepted pause of extension openspec" in output
    assert "(self-acceptance not checked: git cannot read aaaaaaa here)" in output
    assert "accepted_pause=openspec" in output
    assert " self-acceptance-unchecked\n" in output


def test_status_prints_an_operational_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status prints an operational acceptance."""

    _repo, journal, commit = _status_repo(tmp_path, monkeypatch)
    write_record(
        journal,
        "CR-001",
        _operational_record(accepted_commit=commit, accepted_by="test@example.invalid"),
    )

    assert main(["status", "CR-001"]) == 0

    output = capsys.readouterr().out
    assert (
        "Acceptance: accepted operational CR by test@example.invalid "
        "(self-accepted: accepting party is a declared author or committer)" in output
    )
    (record_line,) = (line for line in output.splitlines() if " acceptance " in line)
    assert record_line.endswith(
        f"accepted_commit={commit[:7]} accepted_by=test@example.invalid "
        "operational reason=Switching the extension off is operational "
        "self-accepted"
    )
    assert "findings=" not in record_line


def test_report_derives_accepted_over_findings_only_from_a_findings_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: report derives accepted-over-findings only from an acceptance
    carrying findings."""

    repo = tmp_path / "repo"
    journal = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Pause task"]) == 0
    assert main(["open", "--title", "Operational task"]) == 0
    assert main(["open", "--title", "Accepted task"]) == 0
    write_record(journal, "CR-001", _pause_record(task="CR-001"))
    write_record(journal, "CR-002", _operational_record(task="CR-002"))
    write_record(
        journal,
        "CR-003",
        create_acceptance_record("CR-003", "test", _COMMIT, "op", ["F-1"], "accepted"),
    )
    capsys.readouterr()

    assert main(["report"]) == 0

    output = capsys.readouterr().out
    lines = {line.split("\t")[0]: line for line in output.splitlines()}
    assert "decision" not in lines["CR-001"]
    assert "decision" not in lines["CR-002"]
    assert lines["CR-003"].endswith("\tdecision=accepted-over-findings")


def test_every_output_for_an_acceptance_over_findings_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every output for an acceptance over findings is unchanged.

    The status record line for a findings acceptance is pinned byte for
    byte beside the gate fixtures and the quickstart transcript, which the
    suite pins elsewhere.
    """

    _repo, journal, commit = _status_repo(tmp_path, monkeypatch)
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            commit,
            "test@example.invalid",
            ["F-1", "F-2"],
            "accepted",
        ),
    )

    assert main(["status", "CR-001"]) == 0

    output = capsys.readouterr().out
    (record_line,) = (line for line in output.splitlines() if " acceptance " in line)
    assert record_line.endswith(
        f"accepted_commit={commit[:7]} accepted_by=test@example.invalid "
        "findings=F-1,F-2 reason=accepted self-accepted"
    )
    assert (
        "Acceptance: accepted over findings by test@example.invalid "
        "(self-accepted: accepting party is a declared author or committer)" in output
    )
