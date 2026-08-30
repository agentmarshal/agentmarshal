"""Resolve which actor is creating a record.

ADR-0006: an actor is the party a record is attributed to — a human operator, an
agent, a model reviewer, a CI job — and it is **declared, never authenticated**.
Nothing here establishes that a declared actor corresponds to anyone; until
review records are signed, this is a label like ``vendor`` or ``email``.

What it buys is the separation of two claims the journal conflates today: who is
*said* to have reviewed, and who *created the record*. When an agent records a
human's verdict, the record can now say so instead of being silent.

The value is derived from the environment rather than typed by the caller,
because a field the caller simply fills in adds nothing over the labels that
already exist.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Final

#: Where the value came from, recorded alongside it so an override is visible.
SOURCE_ACTORS_TABLE: Final = "project-actor"
SOURCE_GIT_IDENTITY: Final = "git-identity"
SOURCE_OVERRIDE: Final = "override"

_OVERRIDE_ENV: Final = "AGENTMARSHAL_ACTOR"
_PROJECT_FILE: Final = "project.json"


def _git_identity(project_root: Path) -> str | None:
    """Return the invoking checkout's configured email, or None."""

    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    try:
        identity = result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None
    return identity or None


def _actors_table(project_root: Path) -> dict[str, str]:
    """Map a git identity to an actor id, from an optional project section.

    The section is optional and malformed entries are skipped rather than
    raising: this resolves a label for provenance, and refusing to write a
    record because a convenience table is mistyped would be the wrong trade.
    """

    path = project_root / ".agentmarshal" / _PROJECT_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    section = data.get("actors") if isinstance(data, dict) else None
    if not isinstance(section, dict):
        return {}
    mapping: dict[str, str] = {}
    for actor_id, entry in section.items():
        if not isinstance(actor_id, str) or not isinstance(entry, dict):
            continue
        identities = entry.get("git_identities")
        if not isinstance(identities, list):
            continue
        for identity in identities:
            if isinstance(identity, str) and identity:
                mapping[identity.strip().casefold()] = actor_id
    return mapping


def resolve_recorded_by(project_root: Path) -> tuple[str, str] | None:
    """Return ``(actor, source)`` for the party creating a record, or None.

    Resolution order: an explicit ``AGENTMARSHAL_ACTOR`` override, then the
    project's actors table keyed by the invoking git identity, then that
    identity itself. When nothing can be determined the caller records nothing —
    a guess would be worse than an absent field.
    """

    override = os.environ.get(_OVERRIDE_ENV, "").strip()
    if override:
        return override, SOURCE_OVERRIDE
    identity = _git_identity(project_root)
    if identity is None:
        return None
    actor = _actors_table(project_root).get(identity.strip().casefold())
    if actor is not None:
        return actor, SOURCE_ACTORS_TABLE
    return identity, SOURCE_GIT_IDENTITY
