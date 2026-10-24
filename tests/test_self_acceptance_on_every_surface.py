"""Tests for the self-acceptance mark on the gate and report surfaces.

ADR-0007 decision 4 marks a self-acceptance on every surface that reports
the task; decision 5 has ``report`` say how the completed record's own
binding actually closed (release-audit findings AUD-gate-journal-5 and
-4).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import run_gate
from agentmarshal.journal.records import (
    create_acceptance_record,
    create_completed_record,
    create_finding_record,
    create_review_record,
    write_record,
)
from test_gate import _accept, _gate_repo, _implement, _require_changes
from test_journal import initialize_status_repo


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    A finding record must name its recorder, and CI has neither
    AGENTMARSHAL_ACTOR nor a git identity — so every test sets one the way
    tests/test_status_view.py does, rather than inheriting whatever the
    runner happens to provide.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "tester")


def _report_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """An initialized repo with an opened task, and its journal root."""

    repo = tmp_path / "repo"
    journal_root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    return repo, journal_root


def _commit(repo: Path, name: str) -> str:
    """Commit a file as Test <test@example.invalid> and return its id."""

    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True)
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
            name,
        ],
        cwd=repo,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _review(commit: str, verdict: str, *findings: str) -> dict[str, object]:
    return create_review_record(
        "CR-001",
        "test",
        commit,
        verdict,
        "qa",
        "test",
        "model",
        "reviewer@test.invalid",
        list(findings),
    )


def _report_line(capsys: pytest.CaptureFixture[str], task_id: str) -> str:
    """Run ``report`` and return the task's line."""

    assert main(["report"]) == 0
    (line,) = (
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(f"{task_id}\t")
    )
    return line


@pytest.mark.parametrize("party", ["worker@test.invalid", "Worker@Test.Invalid"])
def test_the_gates_acceptance_line_marks_a_self_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, party: str
) -> None:
    """Scenario: the gate's acceptance line marks a self-acceptance."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by=party)

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        f"PASS: accepted over findings F-001 by {party} (self-accepted: "
        "accepting party is a declared writer of the candidate); "
        "not an approving review"
    ) in output


def test_an_acceptance_by_another_party_prints_unmarked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an acceptance by another party prints unmarked."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by="operator@example.invalid")

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        "PASS: accepted over findings F-001 by operator@example.invalid; "
        "not an approving review"
    ) in output
    assert "self-accepted" not in output

    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", head))
    # A second task whose accepted commit git cannot read answers no mark
    # either — an unanswerable check is not a false "self-accepted".
    assert main(["open", "--title", "Unreadable"]) == 0
    write_record(
        journal,
        "CR-002",
        create_acceptance_record(
            "CR-002",
            "test",
            "a" * 40,
            "worker@test.invalid",
            ["F-1"],
            "accepted",
        ),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )
    assert _report_line(capsys, "CR-002") == (
        "CR-002\topen\treviews=0\ttokens=0\tdecision=accepted-over-findings"
    )


@pytest.mark.parametrize("party", ["test@example.invalid", "Test@Example.Invalid"])
def test_reports_task_line_marks_a_self_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    party: str,
) -> None:
    """Scenario: report's task line marks a self-acceptance."""

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", commit, party, ["F-1"], "accepted"),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0"
        "\tdecision=accepted-over-findings\tself-accepted"
    )


def test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a commit approved after an earlier commit's acceptance reports approved

    The earlier commit's acceptance is even a self-acceptance by party —
    nothing it carries may leak onto the commit that closed on approval.
    """

    _repo, journal = _report_repo(tmp_path, monkeypatch)
    write_record(journal, "CR-001", _review("a" * 40, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            "a" * 40,
            "test@example.invalid",
            ["F-1"],
            "accepted",
        ),
    )
    write_record(journal, "CR-001", _review("b" * 40, "approved"))
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", "b" * 40))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=2\ttokens=0\tdecision=approved"
    )


def test_a_commit_completed_over_findings_reports_accepted_over_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a commit completed over findings reports accepted-over-findings."""

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            commit,
            "operator@example.invalid",
            ["F-1"],
            "accepted",
        ),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_finding_completed_over_findings_reports_accepted_over_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a finding completed over findings reports accepted-over-findings."""

    _repo, journal = _report_repo(tmp_path, monkeypatch)
    finding = write_record(
        journal,
        "CR-001",
        create_finding_record(
            "CR-001",
            "test",
            "A finding",
            [{"ref": "evidence/result.md", "hash": "b" * 64}],
        ),
    ).name.split("-")[0]
    write_record(
        journal,
        "CR-001",
        create_review_record(
            "CR-001",
            "test",
            None,
            "changes_required",
            "qa",
            "test",
            "model",
            "reviewer@test.invalid",
            ["F-1"],
            reviewed_finding=finding,
        ),
    )
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            None,
            "op",
            ["F-1"],
            "accepted",
            accepted_finding=finding,
        ),
    )
    write_record(
        journal,
        "CR-001",
        create_completed_record("CR-001", "test", None, completed_finding=finding),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


def test_an_acceptance_bound_to_another_commit_leaves_no_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an acceptance bound to another commit leaves no decision."""

    _repo, journal = _report_repo(tmp_path, monkeypatch)
    write_record(journal, "CR-001", _review("a" * 40, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", "a" * 40, "op", ["F-1"], "accepted"),
    )
    write_record(journal, "CR-001", _review("b" * 40, "changes_required", "F-2"))
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", "b" * 40))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == ("CR-001\tdone\treviews=2\ttokens=0")


def test_a_task_with_no_completed_record_keeps_todays_decision_rule(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a task with no completed record keeps today's decision rule."""

    _repo, journal = _report_repo(tmp_path, monkeypatch)
    write_record(journal, "CR-001", _review("a" * 40, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", "a" * 40, "op", ["F-1"], "accepted"),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\topen\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )
