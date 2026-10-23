"""Tests for the lead-time phases, rounds and aggregate of ``report``.

ADR-0019 decision 2: the ``opened``, ``review`` and ``completed``
records are written as their event happens, so ``created_at`` is the
event's time; a session's ``started_at`` is its start — and where the
first implementer session lacks it the boundary is ``unknown``, never
substituted with ``created_at``.
"""

from __future__ import annotations

import json
import subprocess
from datetime import timedelta
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_completed_record,
    create_finding_record,
    create_review_record,
    create_session_record,
    write_record,
)
from agentmarshal.journal.report import (
    JournalReport,
    ReviewRound,
    TaskReport,
    format_report,
)

_COMMIT = "a" * 40
_DECLARATION = (
    "A check record is the observer's declaration of what the pipeline found "
    "on the commit, not proof of it."
)


def _initialize_repo(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    # A local identity, so `recorded_by` resolves where a record needs it —
    # CI runs with no global one.
    for arguments in (
        ("config", "user.name", "Recorder"),
        ("config", "user.email", "recorder@test.invalid"),
    ):
        subprocess.run(["git", *arguments], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo / ".agentmarshal" / "journal"


def _open(journal: Path, task_id: str, opened_at: str) -> None:
    """Open *task_id* and restamp its ``opened`` record at *opened_at*.

    ``open`` stamps ``created_at`` with now; the phase lines print the
    record's own time, so a fixture that asserts them needs a known one.
    The record file is rewritten with ``write_record``'s own
    serialization.
    """

    assert main(["open", "--title", f"Task {task_id}"]) == 0
    records_directory = journal / "tasks" / task_id / "records"
    path = next(records_directory.glob("*-opened.json"))
    record = json.loads(path.read_text(encoding="utf-8"))
    record["created_at"] = opened_at
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write(journal: Path, task_id: str, record: dict[str, object], at: str) -> None:
    """Write *record* for *task_id* stamped at *at*."""

    record["created_at"] = at
    write_record(journal, task_id, record)


def _finding(journal: Path, task_id: str, at: str) -> str:
    """Write a finding record for *task_id* stamped at *at*; return its id."""

    finding = create_finding_record(
        task_id,
        "1.0",
        "A finding",
        [{"ref": "evidence/result.md", "hash": "b" * 64}],
    )
    finding["created_at"] = at
    return write_record(journal, task_id, finding).name.split("-")[0]


def _session(
    task_id: str,
    *,
    started_at: str | None = None,
    role: str = "implementer",
) -> dict[str, object]:
    ended_at = None if started_at is None else "2026-10-20T18:00:00Z"
    return create_session_record(
        task_id,
        "1.0",
        role,
        "vendor/model",
        "implementation",
        "implemented",
        10,
        5,
        0,
        started_at=started_at,
        ended_at=ended_at,
    )


def _review(
    task_id: str,
    verdict: str,
    *,
    commit: str = _COMMIT,
    findings: list[str] | None = None,
) -> dict[str, object]:
    return create_review_record(
        task_id,
        "1.0",
        commit,
        verdict,
        "reviewer",
        "vendor",
        "model",
        "reviewer@test.invalid",
        findings or [],
    )


def _completed(task_id: str) -> dict[str, object]:
    return create_completed_record(task_id, "1.0", _COMMIT)


def test_every_boundary_time_prints_with_the_durations_between_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every boundary's time prints, with the durations between
    them."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(
        journal,
        "CR-001",
        _session("CR-001", started_at="2026-10-20T10:30:00Z"),
        "2026-10-20T13:05:00Z",
    )
    finding = _finding(journal, "CR-001", "2026-10-20T10:45:00Z")
    _write(
        journal,
        "CR-001",
        _review("CR-001", "changes_required", findings=[finding]),
        "2026-10-20T11:00:00Z",
    )
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T12:00:00Z")
    _write(journal, "CR-001", _completed("CR-001"), "2026-10-20T13:00:00Z")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "CR-001\tdone\treviews=2\ttokens=15\tusage=unrecorded\tdecision=approved",
        "Phases\topened=2026-10-20T10:00:00Z\timplementer=2026-10-20T10:30:00Z"
        "\treview=2026-10-20T11:00:00Z\tapproval=2026-10-20T12:00:00Z"
        "\tcompleted=2026-10-20T13:00:00Z",
        "Durations\topened->implementer=30m\timplementer->review=30m"
        "\treview->approval=1h\tapproval->completed=1h",
        "Round\t1\tverdict=changes_required\tsince=30m",
        "Round\t2\tverdict=approved\tsince=1h",
        "Cost\tsessions_without_cost=1",
        "Checks\trejected_commits=0",
        _DECLARATION,
    ]


def test_an_implementer_session_without_started_at_is_an_unknown_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an implementer session without started_at is an unknown
    boundary."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(journal, "CR-001", _session("CR-001"), "2026-10-20T14:00:00Z")
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T11:00:00Z")
    _write(journal, "CR-001", _completed("CR-001"), "2026-10-20T13:00:00Z")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    output = capsys.readouterr().out
    assert output.splitlines() == [
        "CR-001\tdone\treviews=1\ttokens=15\tusage=unrecorded\tdecision=approved",
        "Phases\topened=2026-10-20T10:00:00Z\timplementer=unknown"
        "\treview=2026-10-20T11:00:00Z\tapproval=2026-10-20T11:00:00Z"
        "\tcompleted=2026-10-20T13:00:00Z",
        "Durations\topened->implementer=unknown\timplementer->review=unknown"
        "\treview->approval=0s\tapproval->completed=2h",
        "Round\t1\tverdict=approved\tsince=unknown",
        "Cost\tsessions_without_cost=1",
        "Checks\trejected_commits=0",
        _DECLARATION,
    ]
    # The session's write time appears nowhere as a boundary: it is the
    # record's `created_at`, never the run's start (ADR-0019 decision 2).
    assert "2026-10-20T14:00:00Z" not in output


def test_a_boundary_without_a_record_is_not_yet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a boundary without a record is not yet."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "CR-001\topen\treviews=0\ttokens=0",
        "Phases\topened=2026-10-20T10:00:00Z\timplementer=not yet"
        "\treview=not yet\tapproval=not yet\tcompleted=not yet",
        "Durations\topened->implementer=not yet\timplementer->review=not yet"
        "\treview->approval=not yet\tapproval->completed=not yet",
        "Checks\trejected_commits=0",
        _DECLARATION,
    ]


def test_rounds_list_in_order_with_verdicts_and_elapsed_times(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: rounds list in order with verdicts and elapsed times."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(
        journal,
        "CR-001",
        _session("CR-001", started_at="2026-10-20T10:15:00Z"),
        "2026-10-20T14:05:00Z",
    )
    finding = _finding(journal, "CR-001", "2026-10-20T10:30:00Z")
    _write(
        journal,
        "CR-001",
        _review("CR-001", "changes_required", findings=[finding]),
        "2026-10-20T11:00:00Z",
    )
    _write(
        journal,
        "CR-001",
        _review("CR-001", "changes_required", findings=[finding]),
        "2026-10-20T12:30:00Z",
    )
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T14:00:00Z")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    output = capsys.readouterr().out
    rounds = [line for line in output.splitlines() if line.startswith("Round\t")]
    assert rounds == [
        "Round\t1\tverdict=changes_required\tsince=45m",
        "Round\t2\tverdict=changes_required\tsince=1h30m",
        "Round\t3\tverdict=approved\tsince=1h30m",
    ]


def test_a_first_round_after_an_unknown_start_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a first round after an unknown start is unknown."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(journal, "CR-001", _session("CR-001"), "2026-10-20T14:00:00Z")
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T11:00:00Z")
    _open(journal, "CR-002", "2026-10-20T10:00:00Z")
    _write(journal, "CR-002", _review("CR-002", "approved"), "2026-10-20T11:00:00Z")
    capsys.readouterr()

    # A session that cannot say its start, and no session at all, read
    # the same: the first round's elapsed time is unknown.
    assert main(["report", "--task", "CR-001"]) == 0
    rounds = [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("Round\t")
    ]
    assert "\tsince=unknown" in rounds[-1]
    assert main(["report", "--task", "CR-002"]) == 0
    rounds = [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("Round\t")
    ]
    assert rounds == ["Round\t1\tverdict=approved\tsince=unknown"]


def test_the_aggregate_prints_after_todays_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the aggregate prints after today's output."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(
        journal,
        "CR-001",
        _session("CR-001", started_at="2026-10-20T11:00:00Z"),
        "2026-10-20T12:05:00Z",
    )
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T12:00:00Z")
    _write(journal, "CR-001", _completed("CR-001"), "2026-10-20T12:30:00Z")
    _open(journal, "CR-002", "2026-10-20T10:00:00Z")
    _write(journal, "CR-002", _session("CR-002"), "2026-10-20T15:00:00Z")
    _write(journal, "CR-002", _review("CR-002", "approved"), "2026-10-20T12:00:00Z")
    _write(journal, "CR-002", _completed("CR-002"), "2026-10-20T16:00:00Z")
    capsys.readouterr()

    assert main(["report"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "CR-001\tdone\treviews=1\ttokens=15\tusage=unrecorded\tdecision=approved",
        "CR-002\tdone\treviews=1\ttokens=15\tusage=unrecorded\tdecision=approved",
        "Summary\tdone=2\treviews=2\ttokens=30\tusage=unrecorded",
        "Lead\tknown=1\tmedian=2h30m\tmax=2h30m\tunknown=1",
        "Cost\tsessions_without_cost=2",
        "Checks\trejected_commits=0",
        _DECLARATION,
    ]


def test_an_unknown_lead_time_is_counted_never_averaged_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unknown lead time is counted, never averaged in."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(
        journal,
        "CR-001",
        _session("CR-001", started_at="2026-10-20T10:30:00Z"),
        "2026-10-20T11:05:00Z",
    )
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T11:00:00Z")
    _write(journal, "CR-001", _completed("CR-001"), "2026-10-20T12:00:00Z")
    # CR-002's 4h open-to-completion span is known in fact, but its
    # implementer boundary is not — counted unknown, never averaged in.
    _open(journal, "CR-002", "2026-10-20T10:00:00Z")
    _write(journal, "CR-002", _session("CR-002"), "2026-10-20T15:00:00Z")
    _write(journal, "CR-002", _review("CR-002", "approved"), "2026-10-20T11:00:00Z")
    _write(journal, "CR-002", _completed("CR-002"), "2026-10-20T14:00:00Z")
    capsys.readouterr()

    assert main(["report"]) == 0
    lead = [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("Lead\t")
    ]
    assert lead == ["Lead\tknown=1\tmedian=2h\tmax=2h\tunknown=1"]


def test_with_no_fully_known_lead_time_the_median_and_maximum_are_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: with no fully known lead time the median and maximum are
    absent."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(journal, "CR-001", _session("CR-001"), "2026-10-20T15:00:00Z")
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T11:00:00Z")
    _write(journal, "CR-001", _completed("CR-001"), "2026-10-20T14:00:00Z")
    _open(journal, "CR-002", "2026-10-20T09:00:00Z")
    capsys.readouterr()

    assert main(["report"]) == 0
    lead = [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("Lead\t")
    ]
    assert lead == ["Lead\tknown=0\tunknown=1"]


def test_todays_output_is_the_new_outputs_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: today's output is the new output's prefix."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001", "2026-10-20T10:00:00Z")
    _write(
        journal,
        "CR-001",
        _session("CR-001", started_at="2026-10-20T10:30:00Z"),
        "2026-10-20T11:05:00Z",
    )
    _write(journal, "CR-001", _review("CR-001", "approved"), "2026-10-20T11:00:00Z")
    _write(journal, "CR-001", _completed("CR-001"), "2026-10-20T12:00:00Z")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    task_lines = capsys.readouterr().out.splitlines()
    assert task_lines[0] == (
        "CR-001\tdone\treviews=1\ttokens=15\tusage=unrecorded\tdecision=approved"
    )
    assert main(["report"]) == 0
    report_lines = capsys.readouterr().out.splitlines()
    assert report_lines[:-4] == [
        "CR-001\tdone\treviews=1\ttokens=15\tusage=unrecorded\tdecision=approved",
        "Summary\tdone=1\treviews=1\ttokens=15\tusage=unrecorded",
    ]
    assert report_lines[-4:] == [
        "Lead\tknown=1\tmedian=2h\tmax=2h\tunknown=0",
        "Cost\tsessions_without_cost=1",
        "Checks\trejected_commits=0",
        _DECLARATION,
    ]


def test_a_record_value_in_the_new_lines_is_escaped_on_display() -> None:
    """Scenario: a record value in the new lines is escaped on display."""

    task = TaskReport(
        task_id="CR-001",
        state="done",
        review_cycles=1,
        tokens=0,
        rounds=(ReviewRound("approved\nforged", timedelta(minutes=5)),),
    )
    report = JournalReport(tasks=(task,), review_cycles=1, tokens=0)

    lines = format_report(report, include_summary=False)

    assert lines[-3] == "Round\t1\tverdict=approved\\nforged\tsince=5m"
    assert all("\n" not in line for line in lines)
