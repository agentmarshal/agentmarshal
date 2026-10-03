"""The process log: a local working log of process events.

ADR-0014 decisions 1, 2, 6 and 7 and ADR-0022 section 7: appended events
under the clone's local state ``log/`` directory — not evidence, not the
journal, never read by the gate. Every writer appends to a file of its own,
so two processes writing at once never interleave or tear each other's
lines and no lock is needed; each event is one JSON object on one line,
``{"format": 1, "at": <UTC ISO-8601>, "event": <name>, "task"?: <id>, …}``.
A file is rotated when it reaches :data:`ROTATE_AT_BYTES`, with at most
:data:`ROTATED_KEEP` rotated files kept, and the directory as a whole is
bounded by :data:`DIRECTORY_CAP_BYTES` — every process run is a writer, so
per-writer retention alone bounds nothing. The reader tolerates an
unfinished last line, lines that are not JSON objects and event kinds it
does not know, and reads rotated files as well as current ones. Files an
event names — payloads too free-form to be event fields — live in
``files/``, the log directory's one dedicated payload area, beside the
writer files rather than among them. The subdirectory is skipped by the
reader, but the sweep counts its bytes toward the bound: a published
payload sheds at any age — its publish rename is the last write it ever
sees — while a ``.part`` staging file sheds only once it is abandoned,
like a current writer file.
"""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex

from agentmarshal.localstate import LocalState

FORMAT = 1
ROTATE_AT_BYTES = 10 * 1024 * 1024
ROTATED_KEEP = 5
DIRECTORY_CAP_BYTES = 50 * 1024 * 1024
ABANDONED_AFTER_SECONDS = 24 * 60 * 60
FILES_DIR_NAME = "files"
PAYLOAD_STAGING_SUFFIX = ".part"

_NAME_ATTEMPTS = 8

_DAWN = datetime.min.replace(tzinfo=UTC)

_ENVELOPE_KEYS = frozenset({"format", "at", "event", "task"})

_ROTATED_NAME = re.compile(r"\.jsonl\.\d+$")


class ProcessLogError(Exception):
    """Raised when a writer cannot claim a file or an event is refused."""


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
    ever appends to it. Opening also bounds the directory as a whole; the
    sweep runs before this writer's file exists, so it can never take it.
    """

    log_dir = state.ensure_directory(state.log)
    _bound_directory(log_dir)
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
    ``event`` and ``task`` are the writer's envelope — a ``fields`` key
    naming one of them is refused with :class:`ProcessLogError` rather than
    overriding it, and a value strict JSON cannot carry — a non-finite
    number or an unsupported type — is refused the same way before any line
    lands. A naive ``at`` is read as UTC. The file is opened in append mode
    for this one line and closed; an ``OSError`` appending reaches the
    caller as a :class:`ProcessLogError` naming the file and what to do. A
    rotation that fails — a reader can hold the file on Windows — is left
    for the next write to retry; the event is already written.
    """

    stolen = _ENVELOPE_KEYS.intersection(fields)
    if stolen:
        raise ProcessLogError(
            f"event fields may not name the envelope keys: {sorted(stolen)}"
        )
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
    try:
        line = json.dumps(
            record, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError) as error:
        raise ProcessLogError(
            f"event cannot be encoded as strict JSON: {error}"
        ) from error
    try:
        with writer.path.open("ab") as handle:
            handle.write(line.encode("utf-8") + b"\n")
    except OSError as error:
        reason = error.strerror or str(error)
        raise ProcessLogError(
            f"{writer.path}: cannot append the event ({reason}); restore "
            "the file or its directory and retry the write"
        ) from error
    with suppress(OSError):
        _rotate_if_full(writer.path)
    return record


def write_payload(state: LocalState, prefix: str, content: bytes) -> Path:
    """Write *content* as a file under the log directory's ``files/`` area.

    A payload is content an event names by path — review prose, reviewer
    diagnostics — too free-form to be an event field. ``files/`` sits beside
    the writer files rather than among them: the reader reads only regular
    files directly under ``log/``, so a payload's lines can never surface as
    events. The directory is created through the local state's contained
    creation call, the same one the writer uses for ``log/``. The prefix is
    confined to a plain file name — one carrying a path separator is refused
    with :class:`ProcessLogError`, so a payload cannot land outside the
    area. The bytes are written to a ``.part`` staging name and published by
    a rename to the ``.txt`` name the event names, so a file under its final
    name is always complete: the sweep counts it toward the directory bound
    and may shed it at any age, while a staging file counts toward the bound
    too but sheds only once abandoned — younger, a writer may still be
    writing it.
    """

    if Path(prefix).name != prefix:
        raise ProcessLogError(
            f"payload prefix {prefix!r} would land outside the log's "
            f"{FILES_DIR_NAME}/ area"
        )
    files = state.ensure_directory(state.log / FILES_DIR_NAME)
    descriptor, name = tempfile.mkstemp(
        prefix=prefix, suffix=PAYLOAD_STAGING_SUFFIX, dir=files
    )
    staging = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        published = staging.with_suffix(".txt")
        staging.rename(published)
    except OSError:
        with suppress(OSError):
            staging.unlink()
        raise
    return published


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


def _regular_file_info(path: Path) -> os.stat_result | None:
    """The stat of a regular file, ``None`` for anything else or an error."""

    try:
        info = path.stat()
    except OSError:
        return None
    return info if stat.S_ISREG(info.st_mode) else None


def _bound_directory(log_dir: Path) -> None:
    """Delete the directory's oldest files while it exceeds the cap.

    Every process run is a writer of its own, so per-writer retention
    bounds nothing; this bounds the directory — writer files and the
    ``files/`` payload area alike. Candidates go oldest first by
    modification time. A rotated file is a candidate at any age — a writer
    never appends to one again — and so is a published payload, whose
    publish rename is the last write it ever sees. A current ``.jsonl``
    file and a ``.part`` staging file are candidates only once their last
    write is older than :data:`ABANDONED_AFTER_SECONDS`: younger, another
    writer may still be writing them and they are left alone. Everything
    else counts toward the cap but is never deleted, a failed removal is
    skipped and an unreadable entry ignored — the bound is best-effort and
    never fails the open that runs it.
    """

    try:
        entries = list(log_dir.iterdir())
    except OSError:
        return
    cutoff = time.time() - ABANDONED_AFTER_SECONDS
    total = 0
    candidates: list[tuple[float, int, Path]] = []
    for path in entries:
        if path.name == FILES_DIR_NAME and path.is_dir():
            try:
                payloads = list(path.iterdir())
            except OSError:
                continue
            for payload in payloads:
                info = _regular_file_info(payload)
                if info is None:
                    continue
                total += info.st_size
                if payload.suffix != PAYLOAD_STAGING_SUFFIX or info.st_mtime <= cutoff:
                    candidates.append((info.st_mtime, info.st_size, payload))
            continue
        info = _regular_file_info(path)
        if info is None:
            continue
        total += info.st_size
        if _ROTATED_NAME.search(path.name) or (
            path.suffix == ".jsonl" and info.st_mtime <= cutoff
        ):
            candidates.append((info.st_mtime, info.st_size, path))
    candidates.sort()
    for _mtime, size, path in candidates:
        if total <= DIRECTORY_CAP_BYTES:
            return
        try:
            path.unlink()
        except OSError:
            continue
        total -= size


def _rotate_if_full(path: Path) -> None:
    """Rename ``path`` to its next sequence suffix once it reaches the limit.

    Rotated files are ``<name>.1`` … ``<name>.ROTATED_KEEP``: on each
    rotation the suffixes shift up and the oldest file is deleted, so the
    newest rotation is always ``.1``. A rename may fail while a reader
    holds the file; the caller treats any ``OSError`` here as "try again at
    the next write".
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
