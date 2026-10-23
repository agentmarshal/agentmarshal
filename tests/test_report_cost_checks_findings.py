"""Tests for the cost, checks and ``--findings`` additions to ``report``.

The cost lines sum each session's ``cost`` as decimals per currency and
source (ADR-0019 decision 4); the check line counts the distinct commits
a ``check`` record marked ``failed`` or ``error`` names — the observer's
declaration the report says once (ADR-0017 decisions 2 and 3); the
``--findings`` view lists the review ``classes`` and the deferrals still
open (ADR-0016 decisions 1 and 3). Every line the command printed before
this change prints first and unchanged.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_check_record,
    create_completed_record,
    create_review_record,
    create_session_record,
    write_record,
)
from agentmarshal.journal.report import (
    CostSum,
    FindingClassView,
    FindingsReport,
    JournalReport,
    OpenDeferral,
    TaskReport,
    format_findings_report,
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


def _open(journal: Path, task_id: str) -> None:
    """Open a task; the report tests need the record, not a known time."""

    assert main(["open", "--title", f"Task {task_id}"]) == 0
    assert list((journal / "tasks" / task_id / "records").glob("*-opened.json"))


def _write(journal: Path, task_id: str, record: dict[str, object]) -> None:
    write_record(journal, task_id, record)


def _session(task_id: str, *, cost: dict[str, str] | None = None) -> dict[str, object]:
    return create_session_record(
        task_id,
        "1.0",
        "implementer",
        "vendor/model",
        "implementation",
        "implemented",
        10,
        5,
        0,
        cost=cost,
    )


def _check(task_id: str, commit: str, result: str) -> dict[str, object]:
    return create_check_record(task_id, "1.0", commit, "suite", result)


def _review(
    task_id: str,
    *,
    findings: list[str] | None = None,
    advisory_findings: list[str] | None = None,
    classes: dict[str, str] | None = None,
) -> dict[str, object]:
    verdict = "approved" if not findings else "changes_required"
    return create_review_record(
        task_id,
        "1.0",
        _COMMIT,
        verdict,
        "reviewer",
        "vendor",
        "model",
        "reviewer@test.invalid",
        findings or [],
        advisory_findings=advisory_findings,
        classes=classes,
    )


def _completed(
    task_id: str, dispositions: dict[str, dict[str, str]] | None = None
) -> dict[str, object]:
    return create_completed_record(
        task_id, "1.0", _COMMIT, advisory_dispositions=dispositions
    )


def test_cost_sums_print_per_currency_with_reported_and_estimated_apart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: cost sums print per currency with reported and estimated
    apart."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    for cost in (
        {"amount": "1.10", "currency": "USD", "source": "reported"},
        {"amount": "0.50", "currency": "USD", "source": "estimated"},
    ):
        _write(journal, "CR-001", _session("CR-001", cost=cost))
    _write(journal, "CR-001", _review("CR-001"))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Cost\tUSD\treported=1.10\testimated=0.50" in lines
    # The cost lines sit after the round line the view prints today.
    assert lines.index("Cost\tUSD\treported=1.10\testimated=0.50") > lines.index(
        "Round\t1\tverdict=approved\tsince=unknown"
    )


def test_two_currencies_are_two_sums_never_a_blended_figure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: two currencies are two sums, never a blended figure."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    for cost in (
        {"amount": "1.00", "currency": "USD", "source": "reported"},
        {"amount": "4.00", "currency": "EUR", "source": "reported"},
    ):
        _write(journal, "CR-001", _session("CR-001", cost=cost))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Cost\tEUR\treported=4.00" in lines
    assert "Cost\tUSD\treported=1.00" in lines
    assert not any(line.startswith("Cost\t") and "reported=5" in line for line in lines)


def test_amounts_sum_and_print_as_decimals_never_floats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: amounts sum and print as decimals, never floats."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    for amount in ("1.10", "2.20"):
        _write(
            journal,
            "CR-001",
            _session(
                "CR-001",
                cost={"amount": amount, "currency": "USD", "source": "reported"},
            ),
        )
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    # 1.10 + 2.20 is 3.30 as a decimal; a float would print 3.3000000000000003.
    assert "Cost\tUSD\treported=3.30" in lines


def test_amounts_past_the_default_decimal_context_still_sum_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An amount longer than the default context's 28 digits sums exactly.

    The reviewer measured ``123456789012345678901234567890`` + ``1``
    printing ``123456789012345678901234567900`` under the default
    context — a valid amount the record rule admits at any length
    (CR199-DECIMAL-PRECISION).
    """

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    for amount in ("123456789012345678901234567890", "1"):
        _write(
            journal,
            "CR-001",
            _session(
                "CR-001",
                cost={"amount": amount, "currency": "USD", "source": "reported"},
            ),
        )
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert "Cost\tUSD\treported=123456789012345678901234567891" in (
        capsys.readouterr().out.splitlines()
    )


def test_a_task_with_no_cost_shows_none_rather_than_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task with no cost shows none rather than zero."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(journal, "CR-001", _session("CR-001"))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    cost_lines = [line for line in lines if line.startswith("Cost\t")]
    assert cost_lines == ["Cost\tsessions_without_cost=1"]


def test_the_count_of_sessions_carrying_no_cost_prints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the count of sessions carrying no cost prints."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(journal, "CR-001", _session("CR-001"))
    _write(
        journal,
        "CR-001",
        _session(
            "CR-001",
            cost={"amount": "0.00", "currency": "USD", "source": "estimated"},
        ),
    )
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    # A zero cost is a cost — it sums and prints like any other amount;
    # only the genuinely uncosted session counts.
    assert "Cost\tUSD\testimated=0.00" in lines
    assert "Cost\tsessions_without_cost=1" in lines


def test_a_task_holding_no_session_prints_no_cost_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task holding no session prints no cost lines."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert not any(
        line.startswith("Cost\t") for line in capsys.readouterr().out.splitlines()
    )


def test_the_aggregate_sums_every_tasks_sessions_per_currency_and_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the aggregate sums every task's sessions per currency and
    source."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _session(
            "CR-001",
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    _write(
        journal,
        "CR-002",
        _session(
            "CR-002",
            cost={"amount": "2.00", "currency": "USD", "source": "estimated"},
        ),
    )
    capsys.readouterr()

    assert main(["report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Cost\tUSD\treported=1.00\testimated=2.00" in lines
    # The aggregate's cost lines follow the Lead line it prints today.
    assert lines.index("Cost\tUSD\treported=1.00\testimated=2.00") > next(
        index for index, line in enumerate(lines) if line.startswith("Lead\t")
    )


def test_no_conversion_or_blending_across_currencies_in_the_aggregate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no conversion or blending across currencies in the
    aggregate."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _session(
            "CR-001",
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    _write(
        journal,
        "CR-002",
        _session(
            "CR-002",
            cost={"amount": "4.00", "currency": "EUR", "source": "reported"},
        ),
    )
    capsys.readouterr()

    assert main(["report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Cost\tEUR\treported=4.00" in lines
    assert "Cost\tUSD\treported=1.00" in lines


def test_the_aggregate_counts_sessions_carrying_no_cost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the aggregate counts sessions carrying no cost."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(journal, "CR-001", _session("CR-001"))
    _write(journal, "CR-002", _session("CR-002"))
    _write(
        journal,
        "CR-002",
        _session(
            "CR-002",
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    capsys.readouterr()

    assert main(["report"]) == 0
    assert "Cost\tsessions_without_cost=2" in capsys.readouterr().out.splitlines()


def test_with_no_cost_recorded_the_aggregate_prints_no_currency_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: with no cost recorded the aggregate prints no currency
    line."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(journal, "CR-001", _session("CR-001"))
    capsys.readouterr()

    assert main(["report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line for line in lines if line.startswith("Cost\t")] == [
        "Cost\tsessions_without_cost=1"
    ]


def test_the_per_task_count_prints_next_to_the_review_rounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the per-task count prints next to the review rounds."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(journal, "CR-001", _check("CR-001", _COMMIT, "failed"))
    _write(journal, "CR-001", _review("CR-001"))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Checks\trejected_commits=1" in lines
    assert lines.index("Checks\trejected_commits=1") > lines.index(
        "Round\t1\tverdict=approved\tsince=unknown"
    )


def test_distinct_commits_are_counted_not_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: distinct commits are counted, not records."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    # Two refusals on one commit and one on another: three records, two
    # rejected candidates.
    _write(journal, "CR-001", _check("CR-001", "a" * 40, "failed"))
    _write(journal, "CR-001", _check("CR-001", "a" * 40, "error"))
    _write(journal, "CR-001", _check("CR-001", "b" * 40, "failed"))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert "Checks\trejected_commits=2" in capsys.readouterr().out.splitlines()


def test_failed_and_error_count_passed_and_skipped_do_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: failed and error count; passed and skipped do not."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    for commit, result in (
        ("a" * 40, "failed"),
        ("b" * 40, "passed"),
        ("c" * 40, "skipped"),
        ("d" * 40, "error"),
    ):
        _write(journal, "CR-001", _check("CR-001", commit, result))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    assert "Checks\trejected_commits=2" in capsys.readouterr().out.splitlines()


def test_the_aggregate_counts_every_tasks_rejected_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the aggregate counts every task's rejected commits."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(journal, "CR-001", _check("CR-001", "a" * 40, "failed"))
    _write(journal, "CR-001", _check("CR-001", "b" * 40, "error"))
    _write(journal, "CR-002", _check("CR-002", "a" * 40, "failed"))
    capsys.readouterr()

    assert main(["report"]) == 0
    # Each task counts its own distinct commits — two on CR-001 and one
    # on CR-002; the same sha on two tasks is two rejected candidates.
    assert "Checks\trejected_commits=3" in capsys.readouterr().out.splitlines()


def test_the_report_says_once_that_a_check_record_is_the_observers_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the report says once that a check record is the observer's
    declaration."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(journal, "CR-001", _check("CR-001", _COMMIT, "failed"))
    capsys.readouterr()

    assert main(["report"]) == 0
    assert capsys.readouterr().out.count(_DECLARATION) == 1
    assert main(["report", "--task", "CR-001"]) == 0
    assert capsys.readouterr().out.count(_DECLARATION) == 1


def test_todays_report_output_is_the_new_outputs_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: today's report output is the new output's prefix."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(
        journal,
        "CR-001",
        _session(
            "CR-001",
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    _write(journal, "CR-001", _session("CR-001"))
    _write(journal, "CR-001", _check("CR-001", _COMMIT, "failed"))
    _write(journal, "CR-001", _review("CR-001"))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    task_lines = capsys.readouterr().out.splitlines()
    # Every line the view printed before this change still prints first —
    # the new lines are appended, never interleaved.
    assert task_lines[0].startswith("CR-001\t")
    assert task_lines[1].startswith("Phases\topened=")
    assert task_lines[2].startswith("Durations\t")
    assert task_lines[3].startswith("Round\t1\tverdict=approved")
    assert task_lines[4:] == [
        "Cost\tUSD\treported=1.00",
        "Cost\tsessions_without_cost=1",
        "Checks\trejected_commits=1",
        _DECLARATION,
    ]

    assert main(["report"]) == 0
    report_lines = capsys.readouterr().out.splitlines()
    assert report_lines[0].startswith("CR-001\t")
    assert report_lines[1].startswith("Summary\t")
    assert report_lines[2].startswith("Lead\t")
    assert report_lines[3:] == task_lines[4:]


def test_a_record_value_in_the_cost_or_check_lines_is_escaped_on_display() -> None:
    """Scenario: a record value in the cost or check lines is escaped on
    display."""

    task = TaskReport(
        task_id="CR-001",
        state="open",
        review_cycles=0,
        tokens=0,
        sessions=1,
        sessions_without_cost=0,
        costs=(CostSum("US\nD", reported=None, estimated=None),),
    )
    report = JournalReport(tasks=(task,), review_cycles=0, tokens=0)

    lines = format_report(report, include_summary=False)

    assert "Cost\tUS\\nD" in lines
    assert all("\n" not in line for line in lines)


def test_each_class_prints_with_its_count_and_up_to_three_example_finding_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each class prints with its count and up to three example
    finding ids."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(
        journal,
        "CR-001",
        _review(
            "CR-001",
            advisory_findings=["A-1", "A-2", "A-3"],
            classes={"A-1": "style", "A-2": "correctness", "A-3": "style"},
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Classes\tcorrectness\tcount=1\texamples=A-2" in lines
    assert "Classes\tstyle\tcount=2\texamples=A-1,A-3" in lines
    # The classes sort by name, the examples keep the record's order.
    assert lines.index("Classes\tcorrectness\tcount=1\texamples=A-2") < lines.index(
        "Classes\tstyle\tcount=2\texamples=A-1,A-3"
    )


def test_more_than_three_findings_of_a_class_give_three_examples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: more than three findings of a class give three examples."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(
        journal,
        "CR-001",
        _review(
            "CR-001",
            advisory_findings=["A-4", "A-3", "A-2", "A-1"],
            classes={
                "A-4": "style",
                "A-3": "style",
                "A-2": "style",
                "A-1": "style",
            },
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    # The record serializes its `classes` keyed object with sorted keys,
    # so the stored order — and the examples — run A-1 to A-4.
    assert "Classes\tstyle\tcount=4\texamples=A-1,A-2,A-3" in (
        capsys.readouterr().out.splitlines()
    )


def test_classes_are_counted_across_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: classes are counted across tasks."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _review(
            "CR-001",
            advisory_findings=["A-1"],
            classes={"A-1": "correctness"},
        ),
    )
    _write(
        journal,
        "CR-002",
        _review("CR-002", findings=["F-1"], classes={"F-1": "correctness"}),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    assert "Classes\tcorrectness\tcount=2\texamples=A-1,F-1" in (
        capsys.readouterr().out.splitlines()
    )


def test_task_scopes_the_classes_view_to_the_one_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: --task scopes the classes view to the one task."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _review("CR-001", advisory_findings=["A-1"], classes={"A-1": "style"}),
    )
    _write(
        journal,
        "CR-002",
        _review("CR-002", findings=["F-1"], classes={"F-1": "correctness"}),
    )
    capsys.readouterr()

    assert main(["report", "--findings", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Classes\tstyle\tcount=1\texamples=A-1" in lines
    assert not any("correctness" in line for line in lines)


def test_with_no_classes_recorded_the_view_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: with no classes recorded the view says so."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(journal, "CR-001", _review("CR-001"))
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    assert "Classes\t(none)" in capsys.readouterr().out.splitlines()


def test_each_open_deferral_prints_task_finding_id_reason_and_follow_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each open deferral prints task, finding id, reason and
    follow-up."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _completed(
            "CR-001",
            {
                "A-1": {
                    "disposition": "deferred",
                    "reason": "out of scope",
                    "follow_up": "CR-002",
                }
            },
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert (
        "Deferrals\ttask=CR-001\tfinding=A-1\treason=out of scope"
        "\tfollow_up=CR-002 (state: open)" in lines
    )


def test_a_deferral_naming_no_follow_up_task_is_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a deferral naming no follow-up task is open."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(
        journal,
        "CR-001",
        _completed(
            "CR-001",
            {"A-1": {"disposition": "deferred", "reason": "someday"}},
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert (
        "Deferrals\ttask=CR-001\tfinding=A-1\treason=someday\tfollow_up=(none)" in lines
    )


def test_a_deferral_whose_follow_up_the_journal_does_not_hold_is_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a deferral whose follow-up the journal does not hold is
    open."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(
        journal,
        "CR-001",
        _completed(
            "CR-001",
            {
                "A-1": {
                    "disposition": "deferred",
                    "reason": "separate change",
                    "follow_up": "CR-009",
                }
            },
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert any(
        line.endswith("follow_up=CR-009 (not held by the journal)") for line in lines
    )


def test_a_deferral_whose_follow_up_is_held_but_not_completed_is_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a deferral whose follow-up is held but not completed is
    open."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _completed(
            "CR-001",
            {
                "A-1": {
                    "disposition": "deferred",
                    "reason": "queued",
                    "follow_up": "CR-002",
                }
            },
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    assert any(
        line.endswith("follow_up=CR-002 (state: open)")
        for line in capsys.readouterr().out.splitlines()
    )


def test_a_deferral_whose_follow_up_the_journal_holds_as_completed_is_not_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a deferral whose follow-up the journal holds as completed
    is not open."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    _write(
        journal,
        "CR-001",
        _completed(
            "CR-001",
            {
                "A-1": {
                    "disposition": "deferred",
                    "reason": "done there",
                    "follow_up": "CR-002",
                }
            },
        ),
    )
    _write(journal, "CR-002", _completed("CR-002"))
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    assert "Deferrals\t(none)" in capsys.readouterr().out.splitlines()


def test_fixed_and_rejected_entries_are_not_deferrals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: fixed and rejected entries are not deferrals."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _write(
        journal,
        "CR-001",
        _completed(
            "CR-001",
            {
                "A-1": {"disposition": "fixed"},
                "A-2": {"disposition": "rejected", "reason": "not a defect"},
            },
        ),
    )
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Deferrals\t(none)" in lines


def test_with_no_open_deferrals_the_view_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: with no open deferrals the view says so."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    capsys.readouterr()

    assert main(["report", "--findings"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == ["Classes\t(none)", "Deferrals\t(none)"]


def test_a_record_value_in_the_findings_view_is_escaped_on_display() -> None:
    """Scenario: a record value in the findings view is escaped on
    display."""

    report = FindingsReport(
        (FindingClassView("nasty\nclass", 1, ("F-\t1",)),),
        (OpenDeferral("CR-001", "A-1", "see\nattached", "CR-\t9", "state: open"),),
    )

    lines = format_findings_report(report)

    assert lines[0] == "Classes\tnasty\\nclass\tcount=1\texamples=F-\\t1"
    assert lines[1] == (
        "Deferrals\ttask=CR-001\tfinding=A-1\treason=see\\nattached"
        "\tfollow_up=CR-\\t9 (state: open)"
    )
    assert all("\n" not in line for line in lines)
