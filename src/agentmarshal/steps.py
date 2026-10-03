"""The ``step`` command group: announcing and closing in-flight steps.

ADR-0014 decision 9 — as amended 2026-10-03 — and ADR-0022 section 7: the
core records step events in the process log and starts no background
process; the watchdog and the monitor are a supplied component the harness
runs. ``step start`` writes one ``step-started`` event — the step id it
prints, the activity from the session vocabulary, the process and its
start time, and the deadline — and ``step end`` writes one ``step-ended``
event carrying the step id and, when given, the outcome. Both resolve the
journal repository's local state, so a sidecar writes its own log and the
host is never written; neither writes the journal.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TextIO

from agentmarshal.journal.placement import (
    PlacementError,
    resolve_placement,
)
from agentmarshal.journal.records import (
    _SESSION_ACTIVITIES,
    JournalRecordError,
    _is_ulid,
    forges_rendered_text,
    generate_ulid,
    validate_task_id,
)
from agentmarshal.localstate import LocalState, LocalStateError, local_state
from agentmarshal.process_log import (
    ProcessLogError,
    ProcessLogWriter,
    open_writer,
    write_event,
)
from agentmarshal.project import find_project_root

UNKNOWN_PID_STARTED_AT = "unknown"

_DURATION = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class StepError(Exception):
    """Raised when a step command's input cannot be read."""


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``step`` group and its subcommands to *subparsers*."""

    step_parser = subparsers.add_parser(
        "step", help="announce and close in-flight steps"
    )
    step_commands = step_parser.add_subparsers(dest="step_command", required=True)
    start_parser = step_commands.add_parser(
        "start", help="record a step-started event in the process log"
    )
    start_parser.add_argument("--task", required=True, help="task identifier")
    start_parser.add_argument(
        "--activity",
        required=True,
        choices=sorted(_SESSION_ACTIVITIES),
        help="kind of work, from the session activity vocabulary",
    )
    start_parser.add_argument(
        "--deadline",
        required=True,
        help="when the step is due: an ISO-8601 time or a duration such as 90m",
    )
    start_parser.add_argument(
        "--pid",
        type=int,
        default=None,
        help="process the step belongs to (default: this command's parent)",
    )
    start_parser.add_argument("--actor", help="actor running the step")
    start_parser.add_argument("--run-dir", help="directory the step runs in")
    end_parser = step_commands.add_parser(
        "end", help="record a step-ended event in the process log"
    )
    end_parser.add_argument("--task", required=True, help="task identifier")
    end_parser.add_argument("--step", required=True, help="step id to close")
    end_parser.add_argument("--outcome", help="how the step ended — a non-empty word")


def run(args: argparse.Namespace, stderr: TextIO) -> int:
    """Dispatch the parsed ``step`` subcommand."""

    if args.step_command == "start":
        return _run_start(args, stderr)
    if args.step_command == "end":
        return _run_end(args, stderr)
    print(f"step: unknown command {args.step_command}", file=stderr)
    return 1


def _writer_for(command: str, stderr: TextIO) -> ProcessLogWriter | None:
    """Open a writer on the journal repository's local state.

    ``local_state`` always names the git common directory of the repository
    that holds the journal, so in a sidecar the event lands in the
    sidecar's own log and the host never enters the call.
    """

    directory: Path | None = None
    state: LocalState | None = None
    try:
        directory = Path.cwd()
        project_root = find_project_root(directory)
        if project_root is None:
            print(
                f"agentmarshal step {command} must be run inside an "
                "initialized project; run agentmarshal init in the "
                "repository first",
                file=stderr,
            )
            return None
        directory = project_root
        state = local_state(resolve_placement(project_root))
        directory = state.log
        return open_writer(state)
    except (LocalStateError, PlacementError, ProcessLogError, OSError) as error:
        # ``open_writer`` lets an OSError through — a writer file that
        # cannot be claimed — while a ``log/`` a mkdir cannot create
        # arrives as a LocalStateError, and a placement or git failure
        # ahead of them as a PlacementError or LocalStateError. Every
        # refusal ends with what to do: none is left without a path.
        reason = (
            error.strerror or str(error) if isinstance(error, OSError) else str(error)
        )
        if state is not None:
            print(
                f"step {command}: {state.log}: cannot open the process log "
                f"({reason}); check that {state.root} is writable by this "
                "user and has free space, and retry",
                file=stderr,
            )
        else:
            where = directory if directory is not None else Path(".")
            print(
                f"step {command}: {reason}; check that git can run in "
                f"{where} and .agentmarshal/project.json is readable, "
                "then retry",
                file=stderr,
            )
        return None


def _run_start(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        validate_task_id(args.task)
        deadline = _parse_deadline(args.deadline)
        for option, value in (("--actor", args.actor), ("--run-dir", args.run_dir)):
            if value is not None:
                _refuse_unclean_text(value, option)
    except (JournalRecordError, StepError) as error:
        print(f"step start: {error}", file=stderr)
        return 1
    writer = _writer_for("start", stderr)
    if writer is None:
        return 1
    pid = args.pid if args.pid is not None else os.getppid()
    fields: dict[str, Any] = {
        "step": generate_ulid(),
        "activity": args.activity,
        "pid": pid,
        "pid_started_at": pid_started_at(pid),
        "deadline": deadline,
    }
    if args.actor is not None:
        fields["actor"] = args.actor
    if args.run_dir is not None:
        fields["run_dir"] = args.run_dir
    try:
        write_event(writer, "step-started", task=args.task, **fields)
    except ProcessLogError as error:
        print(error, file=stderr)
        return 1
    print(fields["step"])
    return 0


def _run_end(args: argparse.Namespace, stderr: TextIO) -> int:
    try:
        validate_task_id(args.task)
        if not _is_ulid(args.step):
            raise StepError("--step must be a step id of the form step start prints")
    except (JournalRecordError, StepError) as error:
        print(f"step end: {error}", file=stderr)
        return 1
    outcome = args.outcome
    if outcome is not None and not _is_word(outcome):
        print(
            "step end: --outcome must be a non-empty word that cannot "
            "forge rendered text",
            file=stderr,
        )
        return 1
    writer = _writer_for("end", stderr)
    if writer is None:
        return 1
    fields: dict[str, Any] = {"step": args.step}
    if outcome is not None:
        fields["outcome"] = outcome
    try:
        write_event(writer, "step-ended", task=args.task, **fields)
    except ProcessLogError as error:
        print(error, file=stderr)
        return 1
    print(args.step)
    return 0


def _refuse_unclean_text(value: str, option: str) -> None:
    """Raise ``StepError`` when *value* is empty or could forge rendered text.

    ``status`` and ``doctor`` will print these fields inline, so they
    follow the same rule the journal applies to text it renders, which is
    also non-empty: an empty field claims a giver that names nothing.
    """

    if not value:
        raise StepError(f"{option} must be non-empty")
    if forges_rendered_text(value):
        raise StepError(f"{option} must not hold characters that forge rendered text")


def _is_word(value: str) -> bool:
    """Whether *value* is a non-empty word that cannot forge rendered text.

    ``status`` and ``doctor`` will print an outcome inline, so it follows
    the same rule the journal applies to text it renders.
    """

    return (
        bool(value)
        and not any(character.isspace() for character in value)
        and not forges_rendered_text(value)
    )


def _parse_deadline(value: str) -> str:
    """Return *value* as a UTC ISO-8601 timestamp.

    Two spellings: an ISO-8601 time — a naive one reads as UTC, the way the
    writer reads a naive ``at`` — or a duration ``<n><unit>`` measured from
    now, ``unit`` one of ``s``, ``m``, ``h`` and ``d``.
    """

    match = _DURATION.fullmatch(value.strip())
    try:
        if match is not None:
            moment = datetime.now(UTC) + timedelta(
                seconds=int(match.group(1)) * _UNIT_SECONDS[match.group(2)]
            )
        else:
            moment = datetime.fromisoformat(value.strip())
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=UTC)
        return moment.astimezone(UTC).isoformat(timespec="microseconds")
    except (ValueError, OverflowError) as error:
        raise StepError(
            f"deadline {value!r} is neither an ISO-8601 time nor a duration such as 90m"
        ) from error


def pid_started_at(pid: int) -> str:
    """The process's start time as a UTC ISO-8601 timestamp, or ``unknown``.

    Read where the platform exposes it — ``/proc`` on Linux, ``ps -o
    etime=`` on other POSIX systems — and :data:`UNKNOWN_PID_STARTED_AT`
    where it cannot be read, rather than a guess: the field exists to
    disambiguate pid reuse, and a wrong start time defeats it.
    """

    started: datetime | None
    if sys.platform == "linux":
        started = _linux_started_at(pid)
    elif os.name == "posix":
        started = _ps_started_at(pid)
    else:
        started = None
    if started is None:
        return UNKNOWN_PID_STARTED_AT
    return started.astimezone(UTC).isoformat(timespec="seconds")


def _linux_started_at(pid: int) -> datetime | None:
    """Field 22 of ``/proc/<pid>/stat`` plus ``/proc/stat``'s boot time.

    ``comm`` — field 2 — is raw bytes a process names itself with, so the
    file is read as bytes; decoding it would turn a non-ASCII process name
    into a traceback.
    """

    try:
        stat_bytes = Path(f"/proc/{pid}/stat").read_bytes()
    except OSError:
        return None
    # comm may itself hold spaces and parentheses; the fields after its
    # closing ')' begin at field 3, so starttime (field 22) is index 19 of
    # what follows the last one.
    close = stat_bytes.rfind(b")")
    if close < 0:
        return None
    fields = stat_bytes[close + 1 :].split()
    if len(fields) <= 19:
        return None
    try:
        ticks = int(fields[19])
        ticks_per_second = os.sysconf("SC_CLK_TCK")
        boot_time = _boot_time()
    except (OSError, ValueError):
        return None
    if boot_time is None or ticks_per_second <= 0:
        return None
    return datetime.fromtimestamp(boot_time + ticks / ticks_per_second, UTC)


def _boot_time() -> int | None:
    """The ``btime`` line of ``/proc/stat`` as epoch seconds."""

    try:
        lines = Path("/proc/stat").read_bytes().splitlines()
    except OSError:
        return None
    for line in lines:
        if line.startswith(b"btime "):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def _ps_started_at(pid: int) -> datetime | None:
    """POSIX fallback: ``ps -o etime=`` elapsed time subtracted from now.

    The output is captured as bytes and decoded with ``errors="replace"``:
    a byte the locale cannot decode becomes a parse failure — ``unknown``
    — rather than a ``UnicodeDecodeError`` escaping as a traceback.
    """

    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "etime="],
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    elapsed = _elapsed_seconds(result.stdout.decode("utf-8", errors="replace").strip())
    if elapsed is None:
        return None
    return datetime.now(UTC) - timedelta(seconds=elapsed)


def _elapsed_seconds(text: str) -> int | None:
    """Parse ``ps``'s ``etime`` field — ``[[dd-]hh:]mm:ss`` — or None."""

    days = 0
    daypart, separator, rest = text.partition("-")
    if separator:
        if not daypart.isdigit():
            return None
        days = int(daypart)
        text = rest
    parts = text.split(":")
    if not 2 <= len(parts) <= 3 or not all(part.isdigit() for part in parts):
        return None
    seconds = int(parts[-1]) + 60 * int(parts[-2])
    if len(parts) == 3:
        seconds += 3600 * int(parts[0])
    return seconds + 86400 * days
