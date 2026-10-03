"""Tests for the process log (ADR-0014, ADR-0022 section 7)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from typing import cast

import pytest

import agentmarshal.process_log as process_log
from agentmarshal.localstate import LocalState, LocalStateError
from agentmarshal.process_log import open_writer, read_events, write_event

_WRITER_CHILD = """
import sys
from pathlib import Path

from agentmarshal.localstate import LocalState
from agentmarshal.process_log import open_writer, write_event

writer = open_writer(LocalState(Path(sys.argv[1])))
for sequence in range(200):
    write_event(writer, "burst", marker=sys.argv[2], sequence=sequence)
"""


def _put(log_dir: Path, name: str, lines: list[str]) -> Path:
    """Write ``lines`` to ``name``, each newline-terminated."""

    path = log_dir / name
    path.write_bytes(b"".join(line.encode("utf-8") + b"\n" for line in lines))
    return path


def _event_line(**fields: object) -> str:
    record: dict[str, object] = {
        "format": 1,
        "at": "2026-10-03T00:00:00.000000+00:00",
        "event": "made",
    }
    record.update(fields)
    return json.dumps(record)


class _FrozenDatetime(datetime):
    """``datetime`` with ``now`` pinned, for name-collision tests."""

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> _FrozenDatetime:
        return cls(2026, 10, 3, 12, 0, 0, tzinfo=tz)


def test_an_event_lands_as_one_json_object_on_one_line(tmp_path: Path) -> None:
    """Scenario: an event lands as one JSON object on one line."""

    writer = open_writer(LocalState(tmp_path / "agentmarshal"))

    write_event(writer, "step-started", step="01ABC")
    write_event(writer, "step-ended", outcome="completed")

    raw_lines = writer.path.read_bytes().split(b"\n")
    assert raw_lines[-1] == b""
    lines = raw_lines[:-1]
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["format"] == 1
    assert second["format"] == 1
    assert first["event"] == "step-started"
    assert second["event"] == "step-ended"
    at = datetime.fromisoformat(first["at"])
    assert at.tzinfo is not None
    assert at.utcoffset() == timedelta(0)
    assert first["step"] == "01ABC"


def test_a_task_id_rides_along_only_when_given(tmp_path: Path) -> None:
    """Scenario: a task id rides along only when given."""

    writer = open_writer(LocalState(tmp_path / "agentmarshal"))

    write_event(writer, "with-task", task="CR-153")
    write_event(writer, "without-task")

    lines = writer.path.read_bytes().split(b"\n")[:-1]
    assert json.loads(lines[0])["task"] == "CR-153"
    assert "task" not in json.loads(lines[1])


def test_creating_the_writer_makes_the_log_directory_under_the_local_state_root(
    tmp_path: Path,
) -> None:
    """Scenario: the writer's file sits under the local state's log directory."""

    state = LocalState(tmp_path / "agentmarshal")
    assert not state.log.exists()

    writer = open_writer(state)

    assert writer.path.parent == state.log
    assert state.log.is_dir()
    assert writer.path.is_file()


def test_two_writers_never_share_a_file(tmp_path: Path) -> None:
    """Scenario: two writers never share a file."""

    state = LocalState(tmp_path / "agentmarshal")

    first = open_writer(state)
    second = open_writer(state)

    assert first.path != second.path


def test_two_processes_writing_at_once_never_interleave_or_tear_each_others_lines(
    tmp_path: Path,
) -> None:
    """Scenario: concurrent writers never interleave or tear each other's lines."""

    root = tmp_path / "agentmarshal"
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _WRITER_CHILD, str(root), marker],
            stderr=subprocess.PIPE,
        )
        for marker in ("alpha", "beta")
    ]
    for process in processes:
        _, stderr = process.communicate(timeout=120)
        assert process.returncode == 0, stderr

    files = list(LocalState(root).log.iterdir())
    assert len(files) == 2
    for path in files:
        for raw in path.read_bytes().split(b"\n")[:-1]:
            assert isinstance(json.loads(raw), dict)

    events = read_events(LocalState(root))
    assert len(events) == 400
    for marker in ("alpha", "beta"):
        sequences = sorted(
            cast(int, event["sequence"])
            for event in events
            if event["marker"] == marker
        )
        assert sequences == list(range(200))


def test_a_file_that_reaches_the_limit_is_renamed_with_a_sequence_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a file that reaches the limit is renamed with a sequence suffix."""

    monkeypatch.setattr(process_log, "ROTATE_AT_BYTES", 10)
    writer = open_writer(LocalState(tmp_path / "agentmarshal"))
    name = writer.path.name

    write_event(writer, "bulk", sequence=0)
    write_event(writer, "bulk", sequence=1)

    newest = writer.path.with_name(f"{name}.1")
    previous = writer.path.with_name(f"{name}.2")
    assert json.loads(newest.read_bytes().split(b"\n")[0])["sequence"] == 1
    assert json.loads(previous.read_bytes().split(b"\n")[0])["sequence"] == 0
    assert writer.path.name == name
    assert not writer.path.exists()


def test_at_most_five_rotated_files_are_kept_the_oldest_deleted_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: at most five rotated files are kept, the oldest deleted first."""

    monkeypatch.setattr(process_log, "ROTATE_AT_BYTES", 10)
    writer = open_writer(LocalState(tmp_path / "agentmarshal"))
    name = writer.path.name

    for sequence in range(8):
        write_event(writer, "bulk", sequence=sequence)

    rotated = sorted(writer.path.parent.glob(f"{name}.*"))
    assert [path.name for path in rotated] == [
        f"{name}.{number}" for number in range(1, 6)
    ]
    newest = json.loads(writer.path.with_name(f"{name}.1").read_bytes().split(b"\n")[0])
    assert newest["sequence"] == 7
    events = read_events(LocalState(tmp_path / "agentmarshal"))
    assert sorted(cast(int, event["sequence"]) for event in events) == [3, 4, 5, 6, 7]


def test_events_keep_flowing_after_a_rotation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: events keep flowing after a rotation."""

    monkeypatch.setattr(process_log, "ROTATE_AT_BYTES", 100)
    writer = open_writer(LocalState(tmp_path / "agentmarshal"))

    write_event(writer, "before", payload="x" * 200)
    write_event(writer, "after")

    lines = writer.path.read_bytes().split(b"\n")[:-1]
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "after"


def test_events_come_back_in_order_of_at_across_files(tmp_path: Path) -> None:
    """Scenario: events come back in order of at, across files."""

    state = LocalState(tmp_path / "agentmarshal")
    log_dir = state.ensure_directory(state.log)
    _put(
        log_dir,
        "a.jsonl",
        [
            _event_line(at="2026-10-03T10:00:00+00:00", event="late-a"),
            _event_line(at="2026-10-03T12:00:00+00:00", event="latest"),
        ],
    )
    _put(
        log_dir,
        "b.jsonl",
        [_event_line(at="2026-10-03T09:00:00+00:00", event="early")],
    )
    _put(
        log_dir,
        "c.jsonl.2",
        [_event_line(at="2026-10-03T11:00:00+00:00", event="middle")],
    )

    events = read_events(state)

    assert [event["event"] for event in events] == [
        "early",
        "late-a",
        "middle",
        "latest",
    ]


def test_an_unfinished_last_line_is_skipped(tmp_path: Path) -> None:
    """Scenario: an unfinished last line is skipped."""

    state = LocalState(tmp_path / "agentmarshal")
    log_dir = state.ensure_directory(state.log)
    complete = _event_line(at="2026-10-03T09:00:00+00:00", event="complete")
    parseable = _event_line(at="2026-10-03T10:00:00+00:00", event="unterminated")
    torn = '{"format":1,"at":"2026-10-03T11:0'
    (log_dir / "a.jsonl").write_bytes(
        complete.encode("utf-8") + b"\n" + parseable.encode("utf-8")
    )
    (log_dir / "b.jsonl").write_bytes(
        complete.encode("utf-8") + b"\n" + torn.encode("utf-8")
    )

    events = read_events(state)

    assert [event["event"] for event in events] == ["complete", "complete"]


def test_a_line_that_is_not_a_json_object_is_skipped(tmp_path: Path) -> None:
    """Scenario: a line that is not a JSON object is skipped."""

    state = LocalState(tmp_path / "agentmarshal")
    log_dir = state.ensure_directory(state.log)
    _put(
        log_dir,
        "a.jsonl",
        [
            _event_line(at="2026-10-03T09:00:00+00:00", event="kept"),
            "[1, 2, 3]",
            '"a string"',
            "42",
            '{"format":1,"at":',
            "",
            _event_line(at="2026-10-03T10:00:00+00:00", event="also-kept"),
        ],
    )

    events = read_events(state)

    assert [event["event"] for event in events] == ["kept", "also-kept"]


def test_an_event_kind_the_reader_does_not_know_is_kept_as_data(
    tmp_path: Path,
) -> None:
    """Scenario: an event kind the reader does not know is kept as data."""

    state = LocalState(tmp_path / "agentmarshal")
    log_dir = state.ensure_directory(state.log)
    foreign = {
        "format": 1,
        "at": "2026-10-03T09:00:00+00:00",
        "event": "kind-from-the-future",
        "payload": {"nested": [1, "two"]},
    }
    _put(log_dir, "a.jsonl", [json.dumps(foreign)])

    events = read_events(state)

    assert events == [foreign]


def test_rotated_files_are_read_as_well_as_current_ones(tmp_path: Path) -> None:
    """Scenario: rotated files are read as well as current ones."""

    state = LocalState(tmp_path / "agentmarshal")
    log_dir = state.ensure_directory(state.log)
    for suffix, event in ((".2", "oldest"), (".1", "older"), ("", "current")):
        _put(
            log_dir,
            f"w.jsonl{suffix}",
            [_event_line(at="2026-10-03T09:00:00+00:00", event=event)],
        )

    events = read_events(state)

    assert sorted(cast(str, event["event"]) for event in events) == [
        "current",
        "older",
        "oldest",
    ]


def test_a_missing_log_directory_reads_as_empty(tmp_path: Path) -> None:
    """Scenario: a missing log directory reads as empty."""

    assert read_events(LocalState(tmp_path / "agentmarshal")) == []


def test_an_event_without_a_readable_at_is_kept_ordered_first(
    tmp_path: Path,
) -> None:
    """Scenario: an event without a readable at is kept, ordered first."""

    state = LocalState(tmp_path / "agentmarshal")
    log_dir = state.ensure_directory(state.log)
    _put(
        log_dir,
        "a.jsonl",
        [
            _event_line(at="2026-10-03T09:00:00+00:00", event="dated"),
            _event_line(at="not a timestamp", event="bad-at"),
            _event_line(at="2026-10-03", event="naive-ish-at"),
        ],
    )
    no_at = '{"format":1,"event":"no-at"}'
    (log_dir / "b.jsonl").write_bytes(no_at.encode("utf-8") + b"\n")

    events = read_events(state)

    assert [event["event"] for event in events] == [
        "bad-at",
        "naive-ish-at",
        "no-at",
        "dated",
    ]


def test_a_location_outside_the_root_is_refused(tmp_path: Path) -> None:
    """Scenario: a location outside the root is refused."""

    state = LocalState(tmp_path / "agentmarshal")
    outside = tmp_path / "elsewhere"

    with pytest.raises(LocalStateError, match="outside the local state root"):
        state.ensure_directory(outside)

    assert not outside.exists()
    assert not state.root.exists()


def test_a_location_that_escapes_through_dotdot_is_refused(tmp_path: Path) -> None:
    """Scenario: a location that escapes through .. is refused."""

    state = LocalState(tmp_path / "agentmarshal" / "root")
    escape = state.root / ".." / "escaped"

    with pytest.raises(LocalStateError, match="outside the local state root"):
        state.ensure_directory(escape)

    assert not (tmp_path / "agentmarshal" / "escaped").exists()


def test_a_symlink_escape_is_refused(tmp_path: Path) -> None:
    """A symlinked ancestor cannot smuggle a location outside the root.

    The containment check resolves the location first, so ``root/link/x``
    where ``link`` points outside the root is refused even though the
    spelled path begins under it.
    """

    if os.name == "nt":
        pytest.skip("symlink creation needs a privilege Windows may not grant")
    state = LocalState(tmp_path / "agentmarshal" / "root")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    state.ensure_directory(state.root)
    (state.root / "link").symlink_to(elsewhere)

    with pytest.raises(LocalStateError, match="outside the local state root"):
        state.ensure_directory(state.root / "link" / "x")

    assert not (elsewhere / "x").exists()


def test_a_location_under_the_root_is_created(tmp_path: Path) -> None:
    """Scenario: a location under the root is created."""

    state = LocalState(tmp_path / "agentmarshal")

    root = state.ensure_directory(state.root)
    nested = state.ensure_directory(state.log / "deeper" / "still")

    assert root == state.root.resolve()
    assert nested.is_dir()
    assert state.log.is_dir()


def test_importing_the_gate_does_not_import_the_process_log() -> None:
    """Scenario: importing the gate does not import the process log."""

    script = (
        "import sys\n"
        "import agentmarshal.journal.gate\n"
        "assert 'agentmarshal.process_log' not in sys.modules\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_rotation_thresholds_are_module_constants() -> None:
    """The rotation size is 10 MiB and the retention five rotated files.

    Rotation tests patch the constants down; this pins the shipped values.
    """

    assert process_log.ROTATE_AT_BYTES == 10 * 1024 * 1024
    assert process_log.ROTATED_KEEP == 5


def test_writer_file_names_carry_start_time_pid_and_suffix(tmp_path: Path) -> None:
    """A writer's file name records when and which process claimed it.

    The reader never parses names — they are for operators — but the
    identity is what keeps concurrent writers apart.
    """

    writer = open_writer(LocalState(tmp_path / "agentmarshal"))

    stem = writer.path.name[: -len(".jsonl")]
    stamp, pid, token = stem.split("-")
    assert datetime.strptime(stamp, "%Y%m%dT%H%M%S.%fZ").tzinfo is None
    assert pid == str(os.getpid())
    assert len(token) == 16


def test_write_event_normalizes_a_naive_at_to_utc(tmp_path: Path) -> None:
    """An ``at`` passed without a timezone is read as UTC."""

    writer = open_writer(LocalState(tmp_path / "agentmarshal"))

    record = write_event(writer, "pinned", at=datetime(2026, 10, 3, 8, 0, 0))

    assert record["at"] == "2026-10-03T08:00:00.000000+00:00"


def test_open_writer_retries_on_a_name_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A claimed name that already exists yields a different next name."""

    monkeypatch.setattr(process_log, "datetime", _FrozenDatetime)
    tokens = iter(["a" * 16, "a" * 16, "b" * 16])
    monkeypatch.setattr(process_log, "token_hex", lambda _n: next(tokens))
    state = LocalState(tmp_path / "agentmarshal")

    first = open_writer(state)
    second = open_writer(state)

    assert first.path.name.endswith(f"-{'a' * 16}.jsonl")
    assert second.path.name.endswith(f"-{'b' * 16}.jsonl")
    assert second.path.stem.split("-")[0] == first.path.stem.split("-")[0]
