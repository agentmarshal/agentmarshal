"""The process log: a local working log of process events.

ADR-0014 decisions 1, 2, 6 and 7 and ADR-0022 section 7: appended events
under the clone's local state ``log/`` directory — not evidence, not the
journal, never read by the gate. Every writer appends to a file of its own,
so two processes writing at once never interleave or tear each other's
lines and no lock is needed; each event is one JSON object on one line,
``{"format": 1, "at": <UTC ISO-8601>, "event": <name>, "task"?: <id>, …}``.
A file is rotated when it reaches :data:`ROTATE_AT_BYTES`, with at most
:data:`ROTATED_KEEP` rotated files kept; the reader tolerates an unfinished
last line, lines that are not JSON objects and event kinds it does not
know, and reads rotated files as well as current ones.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex

from agentmarshal.localstate import LocalState

FORMAT = 1
ROTATE_AT_BYTES = 10 * 1024 * 1024
ROTATED_KEEP = 5

_NAME_ATTEMPTS = 8

_DAWN = datetime.min.replace(tzinfo=UTC)


class ProcessLogError(Exception):
    """Raised when a writer cannot claim a file of its own."""


@dataclass(frozen=True)
class ProcessLogWriter:
    """One writer's own file under the log directory.

    Obtained from :func:`open_writer`. Only this writer appends to
    ``path`` or rotates it — that exclusivity is what keeps concurrent
    writers' lines whole without a lock.
    """

    path: Path


def open_writer(state: LocalState) -> ProcessLogWriter:
    """Create ``log/`` and claim this writer's own file in it.

    The file's name carries the writer's UTC start time, its process id and
    a random suffix, so no second writer — in this process or another —
    ever appends to it.
    """

    log_dir = state.ensure_directory(state.log)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    for _ in range(_NAME_ATTEMPTS):
        path = log_dir / f"{stamp}-{os.getpid()}-{token_hex(8)}.jsonl"
        try:
            with path.open("xb"):
                pass
        except FileExistsError:
            continue
        return ProcessLogWriter(path)
    raise ProcessLogError(f"{log_dir}: cannot claim a writer file")


def write_event(
    writer: ProcessLogWriter,
    event: str,
    *,
    task: str | None = None,
    at: datetime | None = None,
    **fields: object,
) -> dict[str, object]:
    """Append one event to the writer's file as a single JSON line.

    ``fields`` carries the event kind's own keys; ``format``, ``at``,
    ``event`` and ``task`` are the writer's envelope. A naive ``at`` is read
    as UTC. The file is opened in append mode for this one line and closed.
    """

    stamp = at if at is not None else datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    record: dict[str, object] = {
        "format": FORMAT,
        "at": stamp.astimezone(UTC).isoformat(timespec="microseconds"),
        "event": event,
    }
    if task is not None:
        record["task"] = task
    record.update(fields)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with writer.path.open("ab") as handle:
        handle.write(line.encode("utf-8") + b"\n")
    _rotate_if_full(writer.path)
    return record


def read_events(state: LocalState) -> list[dict[str, object]]:
    """Return every event in the ``log/`` directory, ordered by ``at``.

    Every regular file is read — each writer's current file and its rotated
    ones. A file's last line is skipped unless it is newline-terminated
    (the writer may still hold it), a line that does not parse to a JSON
    object is skipped, and an event kind the reader does not know comes back
    unchanged, as data. An event whose ``at`` is missing, not a string or
    not a readable timestamp is kept and orders before the dated events;
    events sharing an ``at`` keep file-then-line order.
    """

    if not state.log.is_dir():
        return []
    events: list[dict[str, object]] = []
    for path in sorted(state.log.iterdir()):
        if path.is_file():
            events.extend(_file_events(path))
    events.sort(key=_at_or_dawn)
    return events


def _rotate_if_full(path: Path) -> None:
    """Rename ``path`` to its next sequence suffix once it reaches the limit.

    Rotated files are ``<name>.1`` … ``<name>.ROTATED_KEEP``: on each
    rotation the suffixes shift up and the oldest file is deleted, so the
    newest rotation is always ``.1``.
    """

    if path.stat().st_size < ROTATE_AT_BYTES:
        return
    path.with_name(f"{path.name}.{ROTATED_KEEP}").unlink(missing_ok=True)
    for number in range(ROTATED_KEEP - 1, 0, -1):
        rotated = path.with_name(f"{path.name}.{number}")
        if rotated.exists():
            rotated.rename(path.with_name(f"{path.name}.{number + 1}"))
    path.rename(path.with_name(f"{path.name}.1"))


def _file_events(path: Path) -> list[dict[str, object]]:
    try:
        data = path.read_bytes()
    except OSError:
        return []
    lines = data.split(b"\n")
    # The last segment is empty when the file ends with a newline and an
    # unfinished line otherwise — a writer may still be holding it — so it
    # is skipped either way.
    lines.pop()
    events: list[dict[str, object]] = []
    for raw in lines:
        try:
            parsed: object = json.loads(raw.decode("utf-8", errors="replace"))
        except (ValueError, RecursionError):
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    return events


def _at_or_dawn(event: dict[str, object]) -> datetime:
    value = event.get("at")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return _DAWN
        if parsed.tzinfo is not None:
            return parsed
    return _DAWN
