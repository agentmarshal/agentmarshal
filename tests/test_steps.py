"""Tests for the ``agentmarshal step`` command group (ADR-0014 decision 9 as
amended, ADR-0022 section 7)."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.localstate import LocalState
from agentmarshal.process_log import read_events


def _git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo


def _events(repo: Path) -> list[dict[str, object]]:
    return read_events(LocalState(repo / ".git" / "agentmarshal"))


def _tree(root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(root): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _start(*extra: str) -> int:
    return main(
        [
            "step",
            "start",
            "--task",
            "CR-1",
            "--activity",
            "implementation",
            "--deadline",
            "90m",
            *extra,
        ]
    )


def test_a_started_step_lands_as_one_step_started_event_and_its_id_is_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a started step lands as one step-started event and its id
    is printed."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert (
        main(
            [
                "step",
                "start",
                "--task",
                "CR-1",
                "--activity",
                "implementation",
                "--deadline",
                "2030-01-01T00:00:00+00:00",
            ]
        )
        == 0
    )

    step_id = capsys.readouterr().out.strip()
    assert len(step_id) == 26
    events = _events(repo)
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "step-started"
    assert event["task"] == "CR-1"
    assert event["step"] == step_id
    assert event["activity"] == "implementation"
    assert event["pid"] == os.getppid()
    assert event["deadline"] == "2030-01-01T00:00:00.000000+00:00"
    assert "pid_started_at" in event
    assert "actor" not in event
    assert "run_dir" not in event


def test_the_deadline_accepts_an_iso8601_time_or_a_duration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the deadline accepts an ISO-8601 time or a duration."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert (
        main(
            [
                "step",
                "start",
                "--task",
                "CR-1",
                "--activity",
                "review",
                "--deadline",
                "2030-06-15T12:30:00+02:00",
            ]
        )
        == 0
    )
    before = datetime.now(UTC)
    assert _start() == 0
    after = datetime.now(UTC)

    events = _events(repo)
    assert events[0]["deadline"] == "2030-06-15T10:30:00.000000+00:00"
    deadline = datetime.fromisoformat(str(events[1]["deadline"]))
    assert before + timedelta(minutes=90) <= deadline <= after + timedelta(minutes=90)


def test_without_pid_the_parent_process_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: without --pid the parent process is recorded."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert _start() == 0
    assert _start("--pid", "4242") == 0

    events = _events(repo)
    assert events[0]["pid"] == os.getppid()
    assert events[1]["pid"] == 4242


def test_pid_started_at_is_read_or_names_itself_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: pid_started_at is read where the platform allows and names
    itself unknown where it cannot."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()
    # A finished child's pid cannot be read back anywhere.
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()

    assert _start("--pid", str(os.getpid())) == 0
    assert _start("--pid", str(child.pid)) == 0

    events = _events(repo)
    assert len(events) == 2
    started = events[0]["pid_started_at"]
    assert events[1]["pid_started_at"] == "unknown"
    if sys.platform == "linux" or os.name == "posix":
        moment = datetime.fromisoformat(str(started))
        assert moment.tzinfo is not None
        assert moment <= datetime.now(UTC)


def test_actor_and_run_dir_ride_along_only_when_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: actor and run_dir ride along only when given."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert _start("--actor", "impl-1", "--run-dir", "/work/repo") == 0
    assert _start() == 0

    events = _events(repo)
    assert events[0]["actor"] == "impl-1"
    assert events[0]["run_dir"] == "/work/repo"
    assert "actor" not in events[1]
    assert "run_dir" not in events[1]


def test_a_malformed_task_id_an_unknown_activity_or_a_missing_deadline_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed task id, an unknown activity or a missing
    deadline is refused."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert (
        main(
            [
                "step",
                "start",
                "--task",
                "XX-1",
                "--activity",
                "implementation",
                "--deadline",
                "90m",
            ]
        )
        == 1
    )
    assert "task id" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(
            [
                "step",
                "start",
                "--task",
                "CR-1",
                "--activity",
                "gardening",
                "--deadline",
                "90m",
            ]
        )
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(["step", "start", "--task", "CR-1", "--activity", "implementation"])
    capsys.readouterr()
    assert (
        main(
            [
                "step",
                "start",
                "--task",
                "CR-1",
                "--activity",
                "implementation",
                "--deadline",
                "tomorrow",
            ]
        )
        == 1
    )
    assert "ISO-8601" in capsys.readouterr().err

    assert _events(repo) == []


def test_an_ended_step_lands_as_one_step_ended_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an ended step lands as one step-ended event."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert (
        main(["step", "end", "--task", "CR-1", "--step", "01ARZ3NDEKTSV4RRFFQ69G5FAV"])
        == 0
    )
    assert capsys.readouterr().out.strip() == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    assert (
        main(
            [
                "step",
                "end",
                "--task",
                "CR-1",
                "--step",
                "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "--outcome",
                "implemented",
            ]
        )
        == 0
    )

    events = _events(repo)
    assert len(events) == 2
    assert events[0]["event"] == "step-ended"
    assert events[0]["task"] == "CR-1"
    assert events[0]["step"] == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    assert "outcome" not in events[0]
    assert events[1]["outcome"] == "implemented"


def test_an_outcome_that_is_not_a_clean_word_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an outcome that is not a clean word is refused."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    for bad in ("", "two words", "done\u202e"):
        assert (
            main(
                [
                    "step",
                    "end",
                    "--task",
                    "CR-1",
                    "--step",
                    "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                    "--outcome",
                    bad,
                ]
            )
            == 1
        )
        assert "non-empty word" in capsys.readouterr().err

    assert _events(repo) == []


def test_a_step_command_leaves_the_journal_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a step command leaves the journal untouched."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()
    before = _tree(repo / ".agentmarshal")

    assert _start() == 0
    assert main(["step", "end", "--task", "CR-1", "--step", "01ABC"]) == 0

    assert _tree(repo / ".agentmarshal") == before
    assert len(_events(repo)) == 2


def test_in_a_sidecar_the_step_event_lands_in_the_journal_repositorys_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: in a sidecar the step event lands in the journal
    repository's log."""
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    for repo in (host, sidecar):
        repo.mkdir()
        _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    capsys.readouterr()

    assert _start() == 0

    events = read_events(LocalState(sidecar / ".git" / "agentmarshal"))
    assert len(events) == 1
    assert events[0]["event"] == "step-started"
    assert not (host / ".git" / "agentmarshal").exists()


def test_step_help_lists_both_subcommands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The group lists its two subcommands."""

    with pytest.raises(SystemExit) as raised:
        main(["step", "--help"])

    assert raised.value.code == 0
    out = capsys.readouterr().out
    assert "start" in out
    assert "end" in out
