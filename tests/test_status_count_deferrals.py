"""The status view's changes_required count and deferrals (CR-194).

ADR-0016 decision 4: `status` shows the task's count of `changes_required`
verdicts — the same count and threshold the gate's line carries since
CR-168 — flagged when the count reaches the project's threshold; it blocks
nothing. ADR-0016 decision 1: `status` lists the deferrals still open —
each `deferred` finding of the `completed` record's `advisory_dispositions`
with its reason and follow-up task; `fixed` and `rejected` are counted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.records import create_opened_record, write_record
from agentmarshal.journal.status import TaskStatus
from agentmarshal.journal.status_view import print_task_detail


def _project_root(tmp_path: Path, settings: str = "{}") -> Path:
    """A project root carrying a readable ``project.json``."""

    project_root = tmp_path / "project"
    config = project_root / ".agentmarshal"
    config.mkdir(parents=True)
    (config / "project.json").write_text(settings, encoding="utf-8")
    return project_root


def _contract(task_id: str = "CR-001") -> ContractHeader:
    return ContractHeader(
        schema=1, id=task_id, title="Task", scope=("src/",), acceptance=()
    )


def _review(review_id: str, verdict: str, **extra: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": review_id,
        "record_type": "review",
        "created_at": "t",
        "reviewed_commit": "a" * 40,
        "verdict": verdict,
        "findings": [],
        "advisory_findings": [],
    }
    record.update(extra)
    return record


def _held_task(journal_root: Path, task_id: str) -> None:
    """Make the journal hold an open task — directory, contract, `opened`."""

    task_directory = journal_root / "tasks" / task_id
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "+++\n"
        "schema = 1\n"
        f'id = "{task_id}"\n'
        f'title = "{task_id}"\n'
        'scope = ["src/"]\n'
        "acceptance = []\n"
        "+++\n\n# Task\n",
        encoding="utf-8",
    )
    write_record(journal_root, task_id, create_opened_record(task_id, "1.0"))


def test_a_task_without_the_marks_prints_exactly_todays_detail_view(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no count line and no deferrals when the task has neither.

    The byte-for-byte pin: a task with an approved review and a completed
    record without `advisory_dispositions` prints exactly the detail view
    it printed before the lines existed — no `changes_required` line at a
    zero count, no `Deferrals` section.
    """

    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            _review("r-review", "approved", reviewed_commit="b" * 40),
            {
                "id": "r-completed",
                "record_type": "completed",
                "created_at": "t2",
                "completed_commit": "b" * 40,
            },
            {"id": "r-session", "record_type": "session", "created_at": "t3"},
        ),
        state="done",
    )

    print_task_detail(tmp_path, task, tmp_path)

    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: done\n"
        "Title: Task\n"
        "Scope:\n"
        "- src/\n"
        "Records:\n"
        "- r-open opened t0\n"
        "- r-review review t reviewed_commit=bbbbbbb verdict=approved "
        "findings=0 advisory=0\n"
        "- r-completed completed t2 completed_commit=bbbbbbb\n"
        "- r-session session t3\n"
        "No agreement with the contract is recorded\n"
    )


def test_the_count_line_prints_over_every_review_of_the_task(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the count line covers every review of the task's candidates.

    Two `changes_required` verdicts over different commits and one approved
    — the count is 2, below the default threshold 3, so the line names the
    count and the threshold with no mark.
    """

    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            _review("r1", "changes_required", reviewed_commit="a" * 40),
            _review("r2", "changes_required", reviewed_commit="b" * 40),
            _review("r3", "approved", reviewed_commit="c" * 40),
        ),
        state="open",
    )

    print_task_detail(_project_root(tmp_path), task, tmp_path)

    out = capsys.readouterr().out
    assert "changes_required verdicts for CR-001: 2 (threshold 3)\n" in out


def test_a_review_bound_to_a_research_finding_is_not_counted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a review bound to a research finding is not counted.

    Same exclusion the gate applies since CR-168: a `changes_required`
    review carrying `reviewed_finding` (ADR-0009) is not a candidate's
    return — the count is 1, not 2.
    """

    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            _review("r1", "changes_required", reviewed_commit="a" * 40),
            _review("r2", "changes_required", reviewed_finding="F-1", findings=["F-1"]),
        ),
        state="open",
    )

    print_task_detail(_project_root(tmp_path), task, tmp_path)

    out = capsys.readouterr().out
    assert "changes_required verdicts for CR-001: 1 (threshold 3)\n" in out


def test_a_count_at_the_threshold_is_marked(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a count at the threshold is marked.

    Three `changes_required` verdicts against the project's threshold 2 —
    the line carries the same mark the gate prints: the signal to stop and
    revisit the contract.
    """

    project_root = _project_root(
        tmp_path, '{"review": {"changes_required_threshold": 2}}'
    )
    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            _review("r1", "changes_required"),
            _review("r2", "changes_required"),
            _review("r3", "changes_required"),
        ),
        state="open",
    )

    print_task_detail(project_root, task, tmp_path)

    out = capsys.readouterr().out
    assert (
        "changes_required verdicts for CR-001: 3 "
        "(threshold 2 reached — stop and revisit the contract)\n" in out
    )


def test_a_malformed_threshold_is_named_on_the_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed threshold is reported on the line.

    The count still prints and the view does not fail — the line names
    the unreadable threshold, like the gate's line does.
    """

    project_root = _project_root(
        tmp_path, '{"review": {"changes_required_threshold": "high"}}'
    )
    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            _review("r1", "changes_required"),
        ),
        state="open",
    )

    print_task_detail(project_root, task, tmp_path)

    out = capsys.readouterr().out
    assert "changes_required verdicts for CR-001: 1 (threshold unreadable:" in out


def test_each_deferred_finding_is_listed_with_reason_and_follow_up(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each deferred finding is listed with its reason and follow-up.

    `advisory_dispositions` of the `completed` record: two deferrals —
    one naming a follow-up task the journal holds (its state shows), one
    naming a task the journal does not hold (the line says so, not an
    error) — plus one `fixed` and one `rejected`, which are counted on
    one line, not listed.
    """

    journal_root = tmp_path / "journal"
    _held_task(journal_root, "CR-002")
    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            {
                "id": "r-completed",
                "record_type": "completed",
                "created_at": "t1",
                "completed_commit": "b" * 40,
                "advisory_dispositions": {
                    "A-1": {
                        "disposition": "deferred",
                        "reason": "не успели",
                        "follow_up": "CR-002",
                    },
                    "A-2": {
                        "disposition": "deferred",
                        "reason": "отдельная задача",
                        "follow_up": "CR-009",
                    },
                    "A-3": {"disposition": "deferred", "reason": "потом"},
                    "A-4": {"disposition": "fixed"},
                    "A-5": {"disposition": "rejected", "reason": "не дефект"},
                },
            },
        ),
        state="done",
    )

    print_task_detail(tmp_path, task, journal_root)

    out = capsys.readouterr().out
    assert (
        "Deferrals:\n"
        "- A-1: reason=не успели follow_up=CR-002 (state: open)\n"
        "- A-2: reason=отдельная задача follow_up=CR-009 "
        "(not held by the journal)\n"
        "- A-3: reason=потом\n"
        "fixed=1 rejected=1\n" in out
    )


def test_values_from_records_are_escaped_on_display(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every value from a record is escaped on display.

    Built in memory, as in the escaping pin — a reason and a finding id
    carrying characters the forgeable-text rule refuses print escaped on
    the deferral line; they can neither add a line nor reorder one.
    """

    task = TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            {
                "id": "r-completed",
                "record_type": "completed",
                "created_at": "t1",
                "completed_commit": "b" * 40,
                "advisory_dispositions": {
                    "A\u202e1": {
                        "disposition": "deferred",
                        "reason": "one\ntwo\u202e",
                    },
                },
            },
        ),
        state="done",
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert "- A\\u202e1: reason=one\\ntwo\\u202e\n" in out
