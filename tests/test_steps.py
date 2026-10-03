"""Tests for the ``agentmarshal step`` command group (ADR-0014 decision 9 as
amended, ADR-0022 section 7)."""

from __future__ import annotations

import errno
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agentmarshal import steps
from agentmarshal.cli import main
from agentmarshal.localstate import LocalState, LocalStateError
from agentmarshal.process_log import (
    ProcessLogWriter,
    open_writer,
    read_events,
)


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

    out = capsys.readouterr().out
    step_id = out.strip()
    assert out == step_id + "\n"
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


def test_a_proc_stat_with_a_non_ascii_comm_still_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A process name is raw bytes: a ``comm`` with non-ASCII bytes is
    parsed after the last ``)``, never a decode failure."""
    pid = os.getpid()
    stat = b"1234 (\xff\xfeweird (comm)) S " + b"0 " * 18 + b"12345\n"
    real_read_bytes = Path.read_bytes

    def fake_read_bytes(self: Path) -> bytes:
        if self == Path(f"/proc/{pid}/stat"):
            return stat
        return real_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)
    monkeypatch.setattr(steps, "_boot_time", lambda: 1_000_000)
    monkeypatch.setattr(os, "sysconf", lambda _name: 100, raising=False)
    monkeypatch.setattr(sys, "platform", "linux")

    started = steps.pid_started_at(pid)
    expected = datetime.fromtimestamp(1_000_000 + 123.45, UTC)
    assert started == expected.isoformat(timespec="seconds")


def test_the_ps_fallback_parses_etime_and_names_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The portable fallback subtracts ``ps``'s elapsed time from now, and
    output that does not decode or does not parse — or a ``ps`` that
    fails — reads unknown."""
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(os, "name", "posix")
    calls: list[list[str]] = []

    def fake_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, b"1-02:03:04\n", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    before = datetime.now(UTC)
    started = steps.pid_started_at(4321)
    after = datetime.now(UTC)

    assert calls == [["ps", "-p", "4321", "-o", "etime="]]
    elapsed = timedelta(days=1, hours=2, minutes=3, seconds=4)
    moment = datetime.fromisoformat(started)
    # timespec="seconds" truncates, so the read may sit a second early.
    assert before - elapsed - timedelta(seconds=1) <= moment <= after - elapsed

    def garbage_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 0, b"nonsense\n", b"")

    monkeypatch.setattr(subprocess, "run", garbage_run)
    assert steps.pid_started_at(4321) == "unknown"

    def undecodable_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 0, b"\xff\xfe\n", b"")

    monkeypatch.setattr(subprocess, "run", undecodable_run)
    assert steps.pid_started_at(4321) == "unknown"

    def hanging_run(
        command: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(command, 10)

    monkeypatch.setattr(subprocess, "run", hanging_run)
    assert steps.pid_started_at(4321) == "unknown"


def test_a_deadline_that_overflows_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A duration or time beyond ``datetime``'s range is refused with a
    message naming the value and the accepted forms — never a traceback."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    for bad in ("999999999999d", "9999-12-31T23:59:59-12:00"):
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
                    bad,
                ]
            )
            == 1
        )
        error = capsys.readouterr().err
        assert bad in error
        assert "ISO-8601" in error

    assert _events(repo) == []


def test_an_actor_or_run_dir_that_is_empty_or_could_forge_rendered_text_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an actor or run_dir that is empty or could forge rendered
    text is refused."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    for option in ("--actor", "--run-dir"):
        assert _start(option, "") == 1
        assert "non-empty" in capsys.readouterr().err
    for option, value in (
        ("--actor", "impl\u202eactor"),
        ("--run-dir", "line\nbreak"),
    ):
        assert _start(option, value) == 1
        assert "forge rendered text" in capsys.readouterr().err

    assert _events(repo) == []


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
    assert capsys.readouterr().out == "01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
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


def test_a_step_id_that_is_not_a_step_identifier_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a step id that is not a step identifier is refused."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()

    for bad in ("", "not-a-step", "01ABC", "81ARZ3NDEKTSV4RRFFQ69G5FAV"):
        assert main(["step", "end", "--task", "CR-1", "--step", bad]) == 1
        assert "step id" in capsys.readouterr().err

    assert _events(repo) == []


def test_a_step_command_leaves_the_journal_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a step command leaves the journal untouched."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()
    before = _tree(repo / ".agentmarshal")

    assert _start() == 0
    assert (
        main(["step", "end", "--task", "CR-1", "--step", "01ARZ3NDEKTSV4RRFFQ69G5FAV"])
        == 0
    )

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


def test_a_filesystem_failure_opening_the_log_is_a_named_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a filesystem failure opening the log is a named error."""
    repo = _project(tmp_path, monkeypatch)
    capsys.readouterr()
    log_dir = tmp_path / "state" / "log"

    monkeypatch.setattr(
        steps, "local_state", lambda _placement: LocalState(tmp_path / "state")
    )

    def refusing_writer(_state: LocalState) -> ProcessLogWriter:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(steps, "open_writer", refusing_writer)

    assert _start() == 1
    error = capsys.readouterr().err
    assert str(log_dir) in error
    assert "writable" in error
    assert "retry" in error
    assert (
        main(["step", "end", "--task", "CR-1", "--step", "01ARZ3NDEKTSV4RRFFQ69G5FAV"])
        == 1
    )
    error = capsys.readouterr().err
    assert str(log_dir) in error
    assert "writable" in error

    # A ``log/`` that cannot be created — a permission denial or a
    # read-only filesystem — arrives as a LocalStateError rather than an
    # OSError; the refusal still names the directory and what to do.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    blocked_state = LocalState(blocker / "agentmarshal")
    monkeypatch.setattr(steps, "local_state", lambda _placement: blocked_state)
    monkeypatch.setattr(steps, "open_writer", open_writer)

    assert _start() == 1
    error = capsys.readouterr().err
    assert str(blocked_state.log) in error
    assert "writable" in error
    assert (
        main(["step", "end", "--task", "CR-1", "--step", "01ARZ3NDEKTSV4RRFFQ69G5FAV"])
        == 1
    )
    assert "writable" in capsys.readouterr().err

    # A failure before the local state resolves ends with a remedy too.
    def refusing_state(_placement: object) -> LocalState:
        raise LocalStateError(f"{repo}: git cannot name a common directory: stubbed")

    monkeypatch.setattr(steps, "local_state", refusing_state)
    assert _start() == 1
    error = capsys.readouterr().err
    assert "git cannot name a common directory" in error
    assert "retry" in error

    assert _events(repo) == []


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
