"""Capture policy and leak scanning for the supplementary evidence layer.

ADR-0005 Decision 2: a capture policy governs *only* the supplementary
layer (economics, review/prompt text, raw sessions). The always-on
attestation records are outside it, so no policy — not even ``minimal`` —
drops the journal below in-toto Statement completeness (CR-027).

Three rules this module encodes:

* a **preset** (``minimal`` / ``attested`` (default) / ``full``) with
  optional per-class **overrides**;
* raw sessions stay **private by default at every preset**; committing a
  session publicly is a separate escalation that needs *two independent
  opt-ins* — persistent config plus a per-operation flag;
* a **mandatory leak-scan** guards every artifact before it is stored. It
  is a best-effort safeguard, never authorization to publish: callers stay
  private-by-default regardless of what the scan does or does not find.

This module is pure policy: it writes nothing and stores nothing.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


class CaptureError(ValueError):
    """Raised when a capture policy is malformed."""


class CaptureClass(Enum):
    """The supplementary evidence classes a policy governs."""

    ECONOMICS = "economics"
    REVIEWS = "reviews"
    SESSIONS = "sessions"


class CaptureLevel(Enum):
    """How much of a class is captured.

    ``OFF`` captures nothing; ``HASH`` stores a hash-pinned reference into a
    private store; ``COMMIT`` commits the content itself.
    """

    OFF = "off"
    HASH = "hash"
    COMMIT = "commit"


# ADR-0005 Decision 2 preset table. Sessions never exceed HASH by preset —
# public session commit is gated separately by the two opt-ins below.
_PRESETS: Mapping[str, Mapping[CaptureClass, CaptureLevel]] = {
    "minimal": {
        CaptureClass.ECONOMICS: CaptureLevel.OFF,
        CaptureClass.REVIEWS: CaptureLevel.OFF,
        CaptureClass.SESSIONS: CaptureLevel.OFF,
    },
    "attested": {
        CaptureClass.ECONOMICS: CaptureLevel.COMMIT,
        CaptureClass.REVIEWS: CaptureLevel.HASH,
        CaptureClass.SESSIONS: CaptureLevel.HASH,
    },
    "full": {
        CaptureClass.ECONOMICS: CaptureLevel.COMMIT,
        CaptureClass.REVIEWS: CaptureLevel.COMMIT,
        CaptureClass.SESSIONS: CaptureLevel.HASH,
    },
}

DEFAULT_PRESET = "attested"


@dataclass(frozen=True)
class CapturePolicy:
    """A resolved capture policy: a preset, per-class overrides, and flags."""

    preset: str
    overrides: Mapping[CaptureClass, CaptureLevel] = field(default_factory=dict)
    allow_public_sessions: bool = False

    def __post_init__(self) -> None:
        # Defensively copy and freeze the overrides: a frozen dataclass
        # stops field reassignment but not mutation of a mapping the caller
        # still holds a reference to, which could otherwise inject a session
        # COMMIT after construction. Validate the copy, then store the
        # read-only view.
        if not isinstance(self.allow_public_sessions, bool):
            raise CaptureError("allow_public_sessions must be a boolean")
        frozen = MappingProxyType(dict(self.overrides))
        # Sessions are private by default at every preset; committing one
        # publicly is a separate escalation gated by the two opt-ins below,
        # never expressible as a capture level. Reject a session COMMIT
        # override fail-closed so no configuration path can leak a raw
        # session (ADR-0005 Decision 2).
        if frozen.get(CaptureClass.SESSIONS) is CaptureLevel.COMMIT:
            raise CaptureError(
                "sessions cannot be set to 'commit' via a capture override; "
                "public session commit requires allow_public_sessions plus a "
                "per-operation flag"
            )
        object.__setattr__(self, "overrides", frozen)

    def level_for(self, capture_class: CaptureClass) -> CaptureLevel:
        """Return the effective level for a class; an override beats the preset.

        For ``SESSIONS`` this is only ever ``OFF`` or ``HASH`` — a public
        session is never expressed as a level. Use
        :meth:`resolve_session_disposition` for the authoritative session
        decision, which folds in the two-opt-in public gate.
        """

        if capture_class in self.overrides:
            return self.overrides[capture_class]
        return _PRESETS[self.preset][capture_class]

    def may_commit_session_publicly(self, per_operation_flag: bool) -> bool:
        """Whether a raw session may be committed publicly.

        True only when BOTH the persistent ``allow_public_sessions`` config
        and a per-operation flag are set (ADR-0005 supersedes ADR-0004 D7
        for this narrow case). The preset/override path can never yield a
        public session, so this is the sole gate to public session content.
        Both opt-ins must be strict booleans — a truthy non-boolean flag is
        rejected fail-closed rather than silently authorizing a commit.
        """

        if not isinstance(per_operation_flag, bool):
            raise CaptureError("per-operation session flag must be a boolean")
        return self.allow_public_sessions is True and per_operation_flag is True

    def resolve_session_disposition(self, per_operation_flag: bool) -> CaptureLevel:
        """Return the authoritative capture level for a raw session.

        The single API for session disposition: it returns ``COMMIT`` only
        when the two-opt-in public gate is satisfied, and otherwise the
        private preset/override level (``OFF`` or ``HASH``). No caller can
        obtain a public-session decision without both opt-ins.
        """

        if self.may_commit_session_publicly(per_operation_flag):
            return CaptureLevel.COMMIT
        return self.level_for(CaptureClass.SESSIONS)


def _parse_level(value: object, capture_class: CaptureClass) -> CaptureLevel:
    if not isinstance(value, str):
        raise CaptureError(
            f"capture override for {capture_class.value!r} must be a string"
        )
    try:
        return CaptureLevel(value)
    except ValueError as error:
        allowed = ", ".join(level.value for level in CaptureLevel)
        raise CaptureError(
            f"unknown capture level {value!r} for {capture_class.value!r} "
            f"(expected one of {allowed})"
        ) from error


def capture_policy_from_project(project_data: Mapping[str, object]) -> CapturePolicy:
    """Parse a :class:`CapturePolicy` from a project-config object.

    The ``capture`` section is optional; when absent the default
    ``attested`` preset applies, so existing projects are unaffected.
    Fails closed on an unknown preset, class, level, or field.
    """

    section = project_data.get("capture")
    if section is None:
        return CapturePolicy(preset=DEFAULT_PRESET)
    if not isinstance(section, Mapping):
        raise CaptureError("project 'capture' section must be an object")

    allowed_keys = {"preset", "overrides", "allow_public_sessions"}
    unexpected = set(section.keys()) - allowed_keys
    if unexpected:
        raise CaptureError(
            f"capture section has unsupported fields: {', '.join(sorted(unexpected))}"
        )

    preset = section.get("preset", DEFAULT_PRESET)
    if not isinstance(preset, str) or preset not in _PRESETS:
        allowed = ", ".join(sorted(_PRESETS))
        raise CaptureError(
            f"unknown capture preset {preset!r} (expected one of {allowed})"
        )

    overrides: dict[CaptureClass, CaptureLevel] = {}
    raw_overrides = section.get("overrides", {})
    if not isinstance(raw_overrides, Mapping):
        raise CaptureError("capture 'overrides' must be an object")
    for key, value in raw_overrides.items():
        try:
            capture_class = CaptureClass(key)
        except ValueError as error:
            allowed = ", ".join(cls.value for cls in CaptureClass)
            raise CaptureError(
                f"unknown capture class {key!r} (expected one of {allowed})"
            ) from error
        overrides[capture_class] = _parse_level(value, capture_class)

    allow_public_sessions = section.get("allow_public_sessions", False)
    if not isinstance(allow_public_sessions, bool):
        raise CaptureError("capture 'allow_public_sessions' must be a boolean")

    return CapturePolicy(
        preset=preset,
        overrides=overrides,
        allow_public_sessions=allow_public_sessions,
    )


# --- leak scanning --------------------------------------------------------

# Best-effort secret/token signatures. Named so a hit reports *what* class
# was seen without echoing the secret. This is intentionally conservative
# about false negatives being possible (ADR-0005): finding nothing is not a
# guarantee, so callers keep private-by-default.
_LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private-key-block",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"
        ),
    ),
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    (
        "openai-key",
        re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "authorization-header",
        re.compile(r"(?i)authorization:\s*(?:bearer|basic)\s+\S+"),
    ),
)


def scan_for_leaks(
    text: str, private_markers: tuple[str, ...] = ()
) -> list[str]:
    """Return the sorted leak categories found in *text*.

    A best-effort safeguard (ADR-0005): it matches known secret/token
    signatures plus any caller-supplied ``private_markers`` (substrings
    such as an internal hostname). It never echoes the matched secret, only
    the category. An empty result is not proof the text is safe.
    """

    found: set[str] = set()
    for category, pattern in _LEAK_PATTERNS:
        if pattern.search(text):
            found.add(category)
    for marker in private_markers:
        if marker and marker in text:
            found.add("private-marker")
    return sorted(found)


def assert_no_leaks(text: str, private_markers: tuple[str, ...] = ()) -> None:
    """Raise :class:`CaptureError` if *text* trips the leak scan."""

    hits = scan_for_leaks(text, private_markers)
    if hits:
        raise CaptureError(
            f"artifact refused: possible secrets detected ({', '.join(hits)})"
        )
