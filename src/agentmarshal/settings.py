"""The 0.5.0 project settings: one reader, defaults, and named refusals.

ADR-0022 section 6 adds three ``project.json`` keys — the finding-class
vocabulary of ADR-0016 decision 3, the ``changes_required`` threshold of
ADR-0016 decision 4, and ADR-0018's switch making a contract need a recorded
agreement. The consumers land in later tasks (the review launcher, status,
the gate); this module is the one place they all read.

Absent and malformed are different states. An absent key — or an absent
section — returns the documented default. A present but malformed value
raises :class:`ProjectSettingsError` naming the key and what it expects:
``project.json`` is a hand-editable operator surface, and falling back to a
default for a value someone wrote would hide the mistake.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from agentmarshal.journal.contracts import (
    JournalContractError,
    reject_control_characters,
)
from agentmarshal.project import JsonObject, project_file_path, read_project_file

FINDING_CLASSES_KEY: Final = "review.finding_classes"
CHANGES_REQUIRED_THRESHOLD_KEY: Final = "review.changes_required_threshold"
REQUIRE_AGREEMENT_KEY: Final = "contract.require_agreement"

#: The vocabulary of ADR-0016 decision 3.
DEFAULT_FINDING_CLASSES: Final = (
    "correctness",
    "contract-mismatch",
    "claim-accuracy",
    "scope",
    "test-gap",
    "security",
    "style",
)
DEFAULT_CHANGES_REQUIRED_THRESHOLD: Final = 3
DEFAULT_REQUIRE_AGREEMENT: Final = False


class ProjectSettingsError(ValueError):
    """Raised when a project setting is present but malformed."""


@dataclass(frozen=True)
class ProjectSettings:
    """The three 0.5.0 project settings, after defaults and validation."""

    finding_classes: tuple[str, ...]
    changes_required_threshold: int
    require_agreement: bool


def _section(project: JsonObject, name: str, key: str) -> JsonObject | None:
    """Return the section holding *key*, or ``None`` when it is absent.

    A section that is present but not an object is a malformed value like
    any other: the keys under it cannot be read, and treating the section as
    absent would silently substitute the defaults for something an operator
    wrote.
    """

    section = project.get(name)
    if section is None:
        return None
    if not isinstance(section, dict):
        raise ProjectSettingsError(
            f"project.json key {key!r} cannot be read: "
            f"section {name!r} must be an object"
        )
    return cast(JsonObject, section)


def _finding_classes(project: JsonObject) -> tuple[str, ...]:
    section = _section(project, "review", FINDING_CLASSES_KEY)
    value = None if section is None else section.get("finding_classes")
    if value is None:
        return DEFAULT_FINDING_CLASSES
    expected = (
        "a non-empty list of distinct non-empty strings without control characters"
    )
    what = f"project.json key {FINDING_CLASSES_KEY!r}"
    if not isinstance(value, list) or not value:
        raise ProjectSettingsError(f"{what} must be {expected}")
    classes: list[str] = []
    for entry in cast(list[object], value):
        if not isinstance(entry, str) or not entry:
            raise ProjectSettingsError(
                f"{what} entry {entry!r} is not a non-empty string; "
                f"the key must be {expected}"
            )
        if entry in classes:
            raise ProjectSettingsError(
                f"{what} repeats entry {entry!r}; the key must be {expected}"
            )
        try:
            reject_control_characters(entry, f"{what} entry")
        except JournalContractError as error:
            # One predicate, one module error type: the class vocabulary
            # lands in review records and rendered output, so it answers to
            # the same forgeable-text rule contract headers answer to.
            raise ProjectSettingsError(str(error)) from error
        classes.append(entry)
    return tuple(classes)


def _changes_required_threshold(project: JsonObject) -> int:
    section = _section(project, "review", CHANGES_REQUIRED_THRESHOLD_KEY)
    value = None if section is None else section.get("changes_required_threshold")
    if value is None:
        return DEFAULT_CHANGES_REQUIRED_THRESHOLD
    # bool is tested before int: isinstance(True, int) is True.
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ProjectSettingsError(
            f"project.json key {CHANGES_REQUIRED_THRESHOLD_KEY!r} must be "
            "an integer of at least 1"
        )
    return value


def _require_agreement(project: JsonObject) -> bool:
    section = _section(project, "contract", REQUIRE_AGREEMENT_KEY)
    value = None if section is None else section.get("require_agreement")
    if value is None:
        return DEFAULT_REQUIRE_AGREEMENT
    if not isinstance(value, bool):
        raise ProjectSettingsError(
            f"project.json key {REQUIRE_AGREEMENT_KEY!r} must be a boolean"
        )
    return value


def _read(project_root: Path) -> JsonObject:
    return read_project_file(project_file_path(project_root))


def finding_classes(project_root: Path) -> tuple[str, ...]:
    """Read ``review.finding_classes``, or its default when absent."""

    return _finding_classes(_read(project_root))


def changes_required_threshold(project_root: Path) -> int:
    """Read ``review.changes_required_threshold``, or its default."""

    return _changes_required_threshold(_read(project_root))


def require_agreement(project_root: Path) -> bool:
    """Read ``contract.require_agreement``, or its default."""

    return _require_agreement(_read(project_root))


def read_project_settings(project_root: Path) -> ProjectSettings:
    """Read the 0.5.0 project settings from the project's ``project.json``.

    ``project_root`` is the directory the project lookup found — the journal
    repository's root in a sidecar, whose ``project.json`` is the file these
    settings live in. Absent keys fall back to their defaults; a malformed
    one raises :class:`ProjectSettingsError` naming the key and what it
    expects.
    """

    project = _read(project_root)
    return ProjectSettings(
        finding_classes=_finding_classes(project),
        changes_required_threshold=_changes_required_threshold(project),
        require_agreement=_require_agreement(project),
    )
