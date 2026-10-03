"""Tests for ``status`` showing overdue steps and the actual paths.

ADR-0014 decision 9 — as amended 2026-10-03 — and decision 13, and
ADR-0022 section 7: a step is closed by the record it ends with,
``step end`` being an optional addition; ``status`` shows the steps
past their deadline and prints where the journal, the process log and
the local state live.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agentmarshal import steps
from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_opened_record,
    read_records,
    write_record,
)
from agentmarshal.journal.status_view import print_paths
from agentmarshal.localstate import LocalState
from agentmarshal.process_log import open_writer, read_events, write_event
from agentmarshal.steps import OpenStep, format_overdue, open_steps

_STARTED_AT = "2026-01-01T00:00:00+00:00"
_DEADLINE = "2026-01-02T00:00:00+00:00"
_NOW = datetime(2026, 1, 3, tzinfo=UTC)

_CONTRACT = (
    "+++\nschema = 1\nid = '{id}'\ntitle = 'Task'\nscope = []\n"
    "acceptance = []\n+++\n\n# {id}\n"
)


def _started(
    step: str,
    *,
    activity: str = "implementation",
    at: str = _STARTED_AT,
    deadline: str = _DEADLINE,
    task: str = "CR-001",
) -> dict[str, object]:
    return {
        "event": "step-started",
        "task": task,
        "at": at,
        "step": step,
        "activity": activity,
        "deadline": deadline,
    }


def _ended(step: str, *, task: str = "CR-001") -> dict[str, object]:
    return {
        "event": "step-ended",
        "task": task,
        "at": "2026-01-01T01:00:00+00:00",
        "step": step,
    }


def _session(activity: str, created_at: str) -> dict[str, object]:
    return {
        "record_type": "session",
        "activity": activity,
        "created_at": created_at,
    }


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def _task(repo: Path, task_id: str) -> None:
    journal = repo / ".agentmarshal" / "journal"
    task_directory = journal / "tasks" / task_id
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        _CONTRACT.format(id=task_id), encoding="utf-8"
    )
    write_record(journal, task_id, create_opened_record(task_id, "1.0"))


def _state(repo: Path) -> LocalState:
    return LocalState((repo / ".git").resolve() / "agentmarshal")


def _log_step(
    repo: Path,
    step: str,
    *,
    activity: str = "implementation",
    deadline: str = "2026-01-01T00:00:00+00:00",
    task: str = "CR-001",
) -> None:
    writer = open_writer(_state(repo))
    write_event(
        writer,
        "step-started",
        task=task,
        step=step,
        activity=activity,
        pid=1,
        pid_started_at="unknown",
        deadline=deadline,
    )


def _paths_lines(repo: Path) -> str:
    """The three path lines ``status`` prints on stderr for *repo*."""

    state = _state(repo)
    return (
        f"journal: {repo.resolve() / '.agentmarshal' / 'journal'}\n"
        f"process log: {state.log}\n"
        f"local state: {state.root}\n"
    )


def test_a_step_ended_event_closes_the_step() -> None:
    """Scenario: a step-ended event closes the step."""
    events = [_started("S1"), _ended("S1")]

    assert open_steps("CR-001", [], events, now=_NOW) == []


def test_an_implementation_session_closes_an_implementation_step() -> None:
    """Scenario: an implementation session closes an implementation step."""
    records = [_session("implementation", "2026-01-01T01:00:00+00:00")]

    assert open_steps("CR-001", records, [_started("S1")], now=_NOW) == []


def test_a_review_record_closes_a_review_step() -> None:
    """Scenario: a review record closes a review step."""
    events = [_started("S1", activity="review")]
    review = {"record_type": "review", "created_at": "2026-01-01T01:00:00+00:00"}

    assert open_steps("CR-001", [review], events, now=_NOW) == []
    # A session of the same activity does not end a review step — the
    # record a review step ends with is the review itself.
    review_session = _session("review", "2026-01-01T01:00:00+00:00")
    assert open_steps("CR-001", [review_session], events, now=_NOW)


def test_a_session_of_the_activity_closes_a_coordination_or_other_step() -> None:
    """Scenario: a session of the activity closes a coordination or other
    step."""
    for activity in ("coordination", "other"):
        events = [_started("S1", activity=activity)]
        assert open_steps("CR-001", [], events, now=_NOW)
        records = [_session(activity, "2026-01-01T01:00:00+00:00")]
        assert open_steps("CR-001", records, events, now=_NOW) == []
    # A session of a different activity does not close it.
    events = [_started("S1", activity="coordination")]
    records = [_session("other", "2026-01-01T01:00:00+00:00")]
    assert open_steps("CR-001", records, events, now=_NOW)


def test_a_record_written_no_later_than_the_step_started_does_not_close_it() -> None:
    """Scenario: a record written no later than the step started does not
    close it."""
    events = [_started("S1")]
    earlier = [_session("implementation", "2025-12-31T23:00:00+00:00")]
    same = [_session("implementation", _STARTED_AT)]

    assert open_steps("CR-001", earlier, events, now=_NOW)
    assert open_steps("CR-001", same, events, now=_NOW)


def test_an_open_step_inside_its_deadline_is_not_overdue() -> None:
    """Scenario: an open step inside its deadline is not overdue."""
    events = [_started("S1", deadline="2026-01-03T00:00:00+00:00")]

    (step,) = open_steps("CR-001", [], events, now=_NOW)
    assert step.overdue_by is None


def test_an_open_step_past_its_deadline_is_overdue() -> None:
    """A step past its deadline is overdue by the UTC span — the
    complement of the inside-its-deadline scenario."""
    events = [_started("S1")]

    (step,) = open_steps("CR-001", [], events, now=_NOW)
    assert step.step == "S1"
    assert step.activity == "implementation"
    assert step.deadline == _DEADLINE
    assert step.overdue_by == timedelta(days=1)


def test_another_tasks_events_are_not_its_steps() -> None:
    """Scenario: another task's events are not its steps."""
    events = [
        _started("S1", task="CR-999"),
        _ended("S1", task="CR-999"),
    ]

    assert open_steps("CR-001", [], events, now=_NOW) == []
    # The same events do belong to their own task.
    (step,) = open_steps("CR-999", [], events[:1], now=_NOW)
    assert step.step == "S1"


def test_a_step_started_event_that_cannot_name_a_step_reads_as_no_step() -> None:
    """Scenario: a step-started event that cannot name a step reads as no
    step."""
    events = [
        _started("S1"),
        _started("S2"),
        _started("S3"),
    ]
    del events[0]["step"]
    del events[1]["activity"]
    del events[2]["deadline"]

    assert open_steps("CR-001", [], events, now=_NOW) == []


def test_format_overdue_spells_the_span_in_deadline_units() -> None:
    """Verify: the overdue span prints in --deadline's duration units."""
    assert format_overdue(timedelta(minutes=90)) == "1h30m"
    assert format_overdue(timedelta(hours=2, minutes=5)) == "2h5m"
    assert (
        format_overdue(timedelta(days=1, hours=3, minutes=4, seconds=7)) == "1d3h4m7s"
    )
    assert format_overdue(timedelta(seconds=42)) == "42s"


def test_an_overdue_step_prints_its_line_after_the_existing_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an overdue step prints its line after the existing lines."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _log_step(repo, "S1")

    assert main(["status", "CR-001"]) == 0

    lines = capsys.readouterr().out.splitlines()
    overdue = (
        "Overdue step (this machine's process log): step=S1 "
        "activity=implementation deadline=2026-01-01T00:00:00+00:00 past="
    )
    assert lines[-1].startswith(overdue)
    # The line lands after every line the detail prints today — the line
    # before it is the task's last record line.
    assert lines[-2].startswith("- ") and " opened " in lines[-2]


def test_a_task_with_no_overdue_step_prints_no_step_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task with no overdue step prints no step line."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _log_step(repo, "S1", deadline="2999-01-01T00:00:00+00:00")

    assert main(["status", "CR-001"]) == 0

    assert "Overdue" not in capsys.readouterr().out


def test_the_task_list_marks_a_task_that_has_an_overdue_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the task list marks a task that has an overdue step."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _task(repo, "CR-002")
    _log_step(repo, "S1")

    assert main(["status"]) == 0

    lines = capsys.readouterr().out.splitlines()
    first = next(line for line in lines if line.startswith("CR-001"))
    second = next(line for line in lines if line.startswith("CR-002"))
    assert first == "CR-001\topen\tTask\toverdue-step"
    assert second == "CR-002\topen\tTask"


def test_both_forms_take_the_answer_from_one_computation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: both forms take the answer from one computation."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    calls: list[str] = []
    original = open_steps

    def spy(
        task_id: str,
        records: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]],
        *,
        now: datetime | None = None,
    ) -> list[OpenStep]:
        calls.append(task_id)
        return original(task_id, records, events, now=now)

    monkeypatch.setattr(steps, "open_steps", spy)

    assert main(["status"]) == 0
    assert main(["status", "CR-001"]) == 0

    assert calls == ["CR-001", "CR-001"]


def test_both_forms_of_status_print_the_three_paths_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: both forms of status print the three paths once, on
    stderr. Scenario: stdout stays what the documentation promises —
    the paths land on stderr and nothing new reaches stdout."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")

    assert main(["status"]) == 0
    listed = capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    detailed = capsys.readouterr()

    for captured in (listed, detailed):
        assert captured.err == f"Placement: embedded\n{_paths_lines(repo)}"
        assert "journal:" not in captured.out
        assert "process log:" not in captured.out
        assert "local state:" not in captured.out


def test_each_path_prints_escaped_like_other_displayed_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: each path prints escaped like other displayed text."""
    print_paths(Path("jour\nnal"), LocalState(Path("lo\ncal")), None, sys.stderr)

    assert capsys.readouterr().err == (
        "journal: jour\\nnal\nprocess log: lo\\ncal/log\nlocal state: lo\\ncal\n"
    )


def test_in_a_sidecar_the_paths_are_the_journal_repositorys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: in a sidecar the journal and local-state paths are the
    journal repository's."""
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    for directory in (host, sidecar):
        directory.mkdir()
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=directory,
            check=True,
            capture_output=True,
        )
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    assert main(["status"]) == 0

    error_output = capsys.readouterr().err
    state = _state(sidecar)
    assert (
        f"journal: {sidecar.resolve() / '.agentmarshal' / 'journal'}\n"
        f"process log: {state.log}\n"
        f"local state: {state.root}\n"
    ) in error_output
    assert str(host.resolve()) not in error_output


def test_a_missing_process_log_is_not_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing process log is not an error."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")

    assert not _state(repo).log.exists()
    assert main(["status", "CR-001"]) == 0

    captured = capsys.readouterr()
    assert _paths_lines(repo) in captured.err
    assert "Overdue" not in captured.out


def test_a_local_state_that_cannot_be_resolved_is_named_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a local state that cannot be resolved is named
    unavailable."""
    repo = tmp_path / "repo"
    (repo / ".agentmarshal" / "journal" / "tasks" / "CR-001").mkdir(parents=True)
    (repo / ".agentmarshal" / "project.json").write_text(
        '{"schema": 1}\n', encoding="utf-8"
    )
    journal = repo / ".agentmarshal" / "journal"
    (journal / "tasks" / "CR-001" / "contract.md").write_text(
        _CONTRACT.format(id="CR-001"), encoding="utf-8"
    )
    write_record(journal, "CR-001", create_opened_record("CR-001", "1.0"))
    monkeypatch.chdir(repo)

    assert main(["status", "CR-001"]) == 0

    err = capsys.readouterr().err
    assert f"journal: {repo.resolve() / '.agentmarshal' / 'journal'}\n" in err
    assert "process log: unavailable (" in err
    assert "local state: unavailable (" in err


def test_a_task_without_steps_prints_what_it_printed_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task without steps prints on stdout exactly what it
    printed before. Scenario: stdout stays what the documentation
    promises — the byte-exact stdout pin does not move."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    record = read_records(repo / ".agentmarshal" / "journal", "CR-001")[0]

    assert main(["status", "CR-001"]) == 0

    captured = capsys.readouterr()
    # stdout is byte-for-byte the pre-change block; the paths went to
    # stderr.
    assert captured.out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Task\n"
        "Scope:\n"
        "- (none)\n"
        "Records:\n"
        f"- {record['id']} opened {record['created_at']}\n"
    )
    assert captured.err == f"Placement: embedded\n{_paths_lines(repo)}"


def test_status_writes_nothing_into_the_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A status run resolves the paths but creates no log directory."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")

    assert main(["status"]) == 0

    assert not _state(repo).root.exists()


def test_a_completed_or_abandoned_record_closes_the_step() -> None:
    """Scenario: a completed or abandoned record closes the step.

    ADR-0014 decision 9 lists ``completed`` among the records a step
    ends with; ``abandoned`` closes the task the same way.
    """
    events = [_started("S1")]
    for kind in ("completed", "abandoned"):
        record = {
            "record_type": kind,
            "created_at": "2026-01-01T01:00:00+00:00",
        }
        assert open_steps("CR-001", [record], events, now=_NOW) == []
    # Written no later than the step started, even a closing record
    # leaves it open.
    earlier = {"record_type": "completed", "created_at": _STARTED_AT}
    assert open_steps("CR-001", [earlier], events, now=_NOW)


def test_a_process_log_that_cannot_be_read_is_named_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a process log that cannot be read is named on stderr —
    a file where the directory should be."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    state = _state(repo)
    state.root.mkdir(parents=True)
    state.log.write_text("not a directory\n", encoding="utf-8")

    assert main(["status", "CR-001"]) == 0

    captured = capsys.readouterr()
    assert f"process log: {state.log}\n" in captured.err
    assert f"cannot read the process log {state.log} (not a directory)" in (
        captured.err
    )
    assert "Overdue" not in captured.out


@pytest.mark.skipif(
    getattr(os, "geteuid", lambda: -1)() == 0,
    reason="root can read a permission-denied directory",
)
def test_a_permission_denied_process_log_is_named_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a process log that cannot be read is named on stderr —
    a permission denial on the ``log/`` directory."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    state = _state(repo)
    state.log.mkdir(parents=True)
    state.log.chmod(0)

    try:
        assert main(["status", "CR-001"]) == 0
    finally:
        state.log.chmod(0o700)

    captured = capsys.readouterr()
    assert "cannot read the process log" in captured.err
    assert str(state.log) in captured.err
    assert "Overdue" not in captured.out


def test_the_list_indexes_the_step_events_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The list groups the step events by task in one pass — each
    ``open_steps`` call sees its task's own slice, not the whole log."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _task(repo, "CR-002")
    _log_step(repo, "S1")
    index_calls: list[int] = []
    original_index = steps.step_events_by_task
    slices: dict[str, int] = {}
    original_open = open_steps

    def index_spy(
        events: Sequence[Mapping[str, object]],
    ) -> dict[str, list[Mapping[str, object]]]:
        index_calls.append(len(events))
        return original_index(events)

    def open_spy(
        task_id: str,
        records: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]],
        *,
        now: datetime | None = None,
    ) -> list[OpenStep]:
        slices[task_id] = len(events)
        return original_open(task_id, records, events, now=now)

    monkeypatch.setattr(steps, "step_events_by_task", index_spy)
    monkeypatch.setattr(steps, "open_steps", open_spy)

    assert main(["status"]) == 0
    capsys.readouterr()

    assert index_calls == [1]
    # Each task's lookup saw only its own slice — the log is not
    # re-scanned per task.
    assert slices == {"CR-001": 1, "CR-002": 0}


def test_the_process_log_is_read_once_per_status_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the process log is read once per status run, not once
    per task."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _task(repo, "CR-002")
    calls: list[LocalState] = []

    def spy(state: LocalState) -> list[dict[str, object]]:
        calls.append(state)
        return read_events(state)

    monkeypatch.setattr(steps, "read_events", spy)

    assert main(["status"]) == 0
    assert main(["status", "CR-001"]) == 0
    capsys.readouterr()

    assert len(calls) == 2


def test_a_moment_at_the_edge_of_the_range_is_not_a_traceback() -> None:
    """An aware time whose UTC conversion leaves the representable range
    reads as a time that cannot be read — never an OverflowError."""
    # 0001-01-01T00:30:00+01:00 is 0000-12-31 in UTC — below year 1.
    edge = "0001-01-01T00:30:00+01:00"
    events = [_started("S1", at=edge, deadline=edge)]

    (step,) = open_steps("CR-001", [], events, now=_NOW)
    assert step.overdue_by is None
    # An edge-time record cannot be read as written-after either.
    record = _session("implementation", edge)
    assert open_steps("CR-001", [record], [_started("S1")], now=_NOW)
