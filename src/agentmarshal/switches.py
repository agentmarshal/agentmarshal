"""Shared extension switches (ADR-0013 decisions 16 and 17).

A shared extension is switched off only by an operational CR, whose diff
touches only ``.agentmarshal/switches.toml`` — committed next to
``project.json`` on ADR-0014's map of places, the one configuration file
excepted from review. ADR-0022 section 7 gives its shape — a name to
on/off and the reason — and this module fixes the fields: ``format = 1``
and, per extension name, a ``state`` (``on`` or ``off``), the operational
CR that set it (``task``, ``CR-<n>``) and — required when ``off``,
refused when ``on`` — a ``reason`` of at most 1000 characters passing
the forgeable-text rule, the mandatory reason decision 17 writes.

The file is read in two places, each against the extension names its
reader knows: ``stage run`` reads it from the merge base's tree
(decision 6 — a candidate can neither switch a check off for its own
run nor switch one back on), and ``doctor`` reads it from the working
tree. Personal switches — a different file, in the clone's local state —
are a later task; this module reads the shared file only and writes
nothing.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentmarshal.journal.contracts import (
    JournalContractError,
    reject_control_characters,
)

SWITCHES_FORMAT = 1

#: Where the shared switches file lives, on ADR-0014's map of places.
SWITCHES_RELPATH = ".agentmarshal/switches.toml"

#: ADR-0022 section 8's bound on a ``reason`` in the new formats.
REASON_CHAR_LIMIT = 1000

_TASK_PATTERN = re.compile(r"CR-[0-9]+$")

SwitchState = Literal["on", "off"]
_SWITCH_STATES: tuple[SwitchState, ...] = ("on", "off")


class SwitchesError(ValueError):
    """Raised when a switches file is missing the recorded shape.

    ``names`` carries the entry names the file's ``switches`` table
    declares where they could be enumerated — the extensions a refused
    file names, whose stages do not run — and is ``None`` when the file
    is too malformed for its own entries to be read, where it could
    have named anything.
    """

    def __init__(self, message: str, *, names: frozenset[str] | None = None) -> None:
        super().__init__(message)
        self.names = names


@dataclass(frozen=True)
class Switch:
    """One shared extension's switch: its state and the CR that set it."""

    state: Literal["on", "off"]
    task: str
    reason: str | None


def parse_switches(
    data: bytes, source: str | Path, names: Collection[str]
) -> dict[str, Switch]:
    """Parse ``switches.toml`` bytes fail-closed; refusals raise.

    *source* is the text every refusal names — a filesystem path for the
    working tree, a ``<rev>:<path>`` for a base-tree read — and *names*
    the shared extensions the caller knows: an entry naming anything
    else is refused, so a stale entry cannot stand where the file's own
    reader would not recognise it. Byte text that is not UTF-8 TOML, a
    missing or unknown ``format``, a ``switches`` that is not a table,
    an entry that is not a table, an entry naming no known extension,
    a ``state`` outside ``on``/``off``, a ``task`` that is not
    ``CR-<n>``, an ``off`` without a ``reason``, an ``on`` carrying one,
    or a ``reason`` over the character limit or holding a forgeable
    character is each refused naming the file and, where one exists,
    the entry. Keys an entry carries beyond ``state``, ``task`` and
    ``reason`` pass unread — a newer local format may add them.
    """

    shown = str(source)
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise SwitchesError(f"{shown}: malformed: {error}") from error
    table = parsed.get("switches", {})
    declared = frozenset(table) if isinstance(table, dict) else None
    version = parsed.get("format")
    if version is None:
        raise SwitchesError(f"{shown}: missing 'format'", names=declared)
    # `type` and equality both: bool is a subclass of int, so `True` and
    # `1.0` each compare equal to `1` — only an exact int 1 is the known
    # format.
    if not (type(version) is int and version == SWITCHES_FORMAT):
        raise SwitchesError(f"{shown}: unknown format {version!r}", names=declared)
    if not isinstance(table, dict):
        raise SwitchesError(f"{shown}: malformed: 'switches' is not a table")
    switches: dict[str, Switch] = {}
    for name, entry in table.items():
        malformed = f"{shown}: malformed: switch {name!r}"
        if not isinstance(entry, dict):
            raise SwitchesError(f"{malformed} is not a table", names=declared)
        if name not in names:
            raise SwitchesError(
                f"{malformed} names no shared extension", names=declared
            )
        state = entry.get("state")
        task = entry.get("task")
        reason = entry.get("reason")
        if not isinstance(state, str) or state not in _SWITCH_STATES:
            raise SwitchesError(
                f"{malformed} has a 'state' that is not 'on' or 'off'",
                names=declared,
            )
        if not (isinstance(task, str) and _TASK_PATTERN.fullmatch(task)):
            raise SwitchesError(
                f"{malformed} has a 'task' that is not a CR identifier",
                names=declared,
            )
        reason_value: str | None = None
        if state == "off":
            if not isinstance(reason, str) or not reason:
                raise SwitchesError(
                    f"{malformed} is 'off' without a 'reason'", names=declared
                )
            if len(reason) > REASON_CHAR_LIMIT:
                raise SwitchesError(
                    f"{malformed} has a 'reason' over {REASON_CHAR_LIMIT} characters",
                    names=declared,
                )
            try:
                reject_control_characters(reason, f"switch {name!r} field 'reason'")
            except JournalContractError as error:
                raise SwitchesError(
                    f"{shown}: malformed: {error}", names=declared
                ) from error
            reason_value = reason
        elif reason is not None:
            raise SwitchesError(
                f"{malformed} is 'on' and carries a 'reason'", names=declared
            )
        switches[name] = Switch(state=state, task=task, reason=reason_value)
    return switches


def read_switches(path: Path, names: Collection[str]) -> dict[str, Switch]:
    """Read the working tree's switches file; a missing file is all-on."""

    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise SwitchesError(
            f"{path}: cannot read the switches file: {error.strerror or error}"
        ) from error
    return parse_switches(data, path, names)
