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

The leak scan defends additions in a candidate before they are stored or
published. It does not defend content already in the tree, removed content, or
any other publication path. It is best-effort by design (ADR-0005): no pattern
list can enumerate every secret, so a clean scan can never be permission to
publish. Callers remain private-by-default regardless of the result.

For the policy parsers, ``project.json`` is operator input read from a trusted
tree, not contributor input. The gate reads it from the base side for exactly
that reason.

This module is pure policy: it writes nothing and stores nothing.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from agentmarshal.project import PROJECT_CONFIG_RELPATH


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
        # The constructor is a public construction path (tests and callers
        # build policies directly), so it fully validates rather than trust
        # the parser: an invalid preset, override key, or override value
        # must fail closed here, not surface later as a KeyError or a level
        # that is not a CaptureLevel.
        if self.preset not in _PRESETS:
            allowed = ", ".join(sorted(_PRESETS))
            raise CaptureError(
                f"unknown capture preset {self.preset!r} (expected one of {allowed})"
            )
        if not isinstance(self.allow_public_sessions, bool):
            raise CaptureError("allow_public_sessions must be a boolean")
        frozen = MappingProxyType(dict(self.overrides))
        for key, value in frozen.items():
            if not isinstance(key, CaptureClass):
                raise CaptureError(
                    f"capture override key must be a CaptureClass: {key!r}"
                )
            if not isinstance(value, CaptureLevel):
                raise CaptureError(
                    f"capture override value must be a CaptureLevel: {value!r}"
                )
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
        # Matches PKCS#8 (BEGIN PRIVATE KEY), algorithm-tagged forms (RSA,
        # EC, DSA, OPENSSH), ENCRYPTED PKCS#8, and PGP PRIVATE KEY BLOCK.
        re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----"),
    ),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
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


@dataclass(frozen=True, order=True)
class LeakHit:
    """One location-safe leak-scan result.

    ``identification`` is either a public built-in signature name or a private
    marker's one-based configured position.  It deliberately never holds the
    matched text or a marker value.

    Neither does ``path``: a repository can have a directory named after an
    internal host, and a file can be named after the very key a signature
    matches, so a path can be the secret. Naming such a file would disclose
    what naming the marker or withholding the matched text refused to. In
    those paths :func:`safe_path` replaces the offending span with a
    description of it, and the rest of the path still says where.
    """

    path: str
    identification: str


def safe_path(path: str, private_markers: tuple[str, ...]) -> str:
    """Return *path* with anything secret in it replaced by a description.

    A configured marker is named by position and a built-in signature by its
    own identifier, exactly as in ``identification``: the description says
    what the path carries and never the characters it carries.

    Only the offending span is replaced, so the rest of the path still says
    where. Describing the whole path instead made two leaking files under one
    marker-named directory render identically and collapse into one hit —
    losing the "where" this scan exists to give.
    """

    safe = path
    for index, marker in enumerate(private_markers, start=1):
        if marker and marker in safe:
            safe = safe.replace(marker, f"<private marker #{index}>")
    for category, pattern in _LEAK_PATTERNS:
        safe = pattern.sub(f"<{category}>", safe)
    return safe


# A caller may render hits into a bounded document (the merge transcript) or
# use them as its whole output (the standalone command). The caller owns that
# choice; this renderer owns only the common, location-safe hit shape.
def render_leak_hits(hits: list[LeakHit], limit: int | None) -> str:
    """Render hit records without exposing matched content.

    The standalone command and merge gate both use this one renderer: warning
    detail therefore cannot silently diverge between their two call sites.
    """

    shown = hits if limit is None else hits[:limit]
    rendered = ", ".join(f"{hit.path}: {hit.identification}" for hit in shown)
    remaining = len(hits) - len(shown)
    if remaining > 0:
        return f"{rendered}, and {remaining} more not shown"
    return rendered


def scan_for_leaks(text: str, private_markers: tuple[str, ...] = ()) -> list[str]:
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


_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


def _diff_path(header: str) -> str | None:
    """Return the destination path from a unified-diff ``+++`` header."""

    if not header.startswith("+++ "):
        return None
    path = header[4:]
    if path == "/dev/null":
        return None
    # git's default destination prefix. Both callers pass --dst-prefix=b/ for
    # exactly this reason. A diff from anywhere else may still arrive with
    # another prefix, or C-quoted for a non-ASCII path, and the path is then
    # taken as given: a wrong-looking path in a warning is a smaller fault
    # than a stripped first character.
    return path[2:] if path.startswith("b/") else path


def _signature_hits(added_text: str, path: str) -> set[LeakHit]:
    """Return built-in-signature hits over one file's added text.

    Whole text rather than line by line: a signature may span a wrapped header,
    and an earlier draft of this change narrowed those by matching each line on
    its own.
    """

    return {
        LeakHit(path, signature)
        for signature, pattern in _LEAK_PATTERNS
        if pattern.search(added_text)
    }


def scan_diff_for_leaks(
    unified_diff: str,
    private_markers: tuple[str, ...] = (),
    *,
    config_path: str = PROJECT_CONFIG_RELPATH,
) -> list[LeakHit]:
    """Return location-safe leak hits from the *added* lines of a unified diff.

    Only lines the diff introduces are scanned, so this is forward-only leak
    prevention: content already in the tree (including consciously accepted
    historical residuals) and removed lines are never re-flagged.

    Parsing follows the hunk line counts from each ``@@ -a,b +c,d @@`` header
    rather than a prefix test, so it is correct for any unified diff, not just
    one exact ``git diff`` shape. Inside a hunk body an added line is consumed
    by the new-side counter and a removed line by the old-side counter; the
    body ends when both counts are exhausted, so file headers between patches
    (``---``/``+++``) are never mistaken for content. This also means an added
    line whose content itself starts with ``+`` (emitted as ``+++…``) is still
    scanned — a secret cannot hide behind leading plus signs. Pure: it parses
    the text it is given and runs nothing. As with :func:`scan_for_leaks` an
    empty result is not proof of safety.
    """

    hits: set[LeakHit] = set()
    marker_occurrences: dict[int, list[str]] = {
        index: [] for index, marker in enumerate(private_markers, start=1) if marker
    }
    # A real git diff always names the destination before a hunk.  Retaining a
    # safe placeholder lets the pure parser still report a hand-written hunk
    # used by callers/tests rather than silently omitting a detected signature.
    # The same placeholder covers a destination of /dev/null: a scanner that
    # stopped scanning because it had no name for the file would fail open.
    current_path = "(unknown file)"
    # Added lines are collected per file and matched together: a signature may
    # span more than one line, and attribution still needs the file.
    added_by_path: dict[str, list[str]] = {}
    lines = unified_diff.splitlines()
    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        if line.startswith("+++ "):
            current_path = _diff_path(line) or "(unknown file)"
        header = _HUNK_HEADER.match(line)
        index += 1
        if header is None:
            continue
        old_remaining = int(header.group(1)) if header.group(1) is not None else 1
        new_remaining = int(header.group(2)) if header.group(2) is not None else 1
        while index < total and (old_remaining > 0 or new_remaining > 0):
            body = lines[index]
            index += 1
            if body.startswith("\\"):
                # "\ No newline at end of file" — not a content line.
                continue
            if body.startswith("+"):
                added_by_path.setdefault(current_path, []).append(body[1:])
                new_remaining -= 1
            elif body.startswith("-"):
                old_remaining -= 1
            else:
                # A context line (leading space) belongs to both sides.
                old_remaining -= 1
                new_remaining -= 1
    # Occurrences inside the file that declares the markers are not reported;
    # every occurrence outside it is. design.md records this as a departure
    # from the contract's "sole occurrence" wording: the declaration's path is
    # where a marker is defined, never where it leaked.
    for path, added_lines in added_by_path.items():
        added_text = "\n".join(added_lines)
        hits.update(_signature_hits(added_text, safe_path(path, private_markers)))
        for marker_index, marker in enumerate(private_markers, start=1):
            if marker and marker in added_text:
                marker_occurrences[marker_index].append(path)
    for marker_index, occurrences in marker_occurrences.items():
        elsewhere = {path for path in occurrences if path != config_path}
        if not elsewhere:
            # Every occurrence is in the configuration that declares the
            # marker. That is the declaration matching itself, which is what
            # this rule exists to drop.
            continue
        # The declaration's own path is not reported beside a real occurrence:
        # it is where the marker is defined, not where it leaked.
        for path in elsewhere:
            hits.add(
                LeakHit(
                    safe_path(path, private_markers), f"private-marker #{marker_index}"
                )
            )
    return sorted(hits)


def private_markers_from_project(
    project_data: Mapping[str, object],
) -> tuple[str, ...]:
    """Parse the optional ``leak_scan.private_markers`` list from project config.

    An absent ``leak_scan`` section yields no markers, so the scan falls back
    to the built-in secret signatures only and existing projects are
    unaffected. Fails closed on a malformed section (a non-object
    ``leak_scan``, an unsupported field, a non-list ``private_markers``, or a
    non-string / empty entry) rather than silently ignoring it.
    """

    section = project_data.get("leak_scan")
    if section is None:
        return ()
    if not isinstance(section, Mapping):
        raise CaptureError("project 'leak_scan' section must be an object")

    allowed_keys = {"private_markers"}
    unexpected = set(section.keys()) - allowed_keys
    if unexpected:
        raise CaptureError(
            f"leak_scan section has unsupported fields: {', '.join(sorted(unexpected))}"
        )

    raw = section.get("private_markers", [])
    if not isinstance(raw, list):
        raise CaptureError("leak_scan 'private_markers' must be a list")
    markers: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item:
            raise CaptureError(
                "leak_scan 'private_markers' entries must be non-empty strings"
            )
        markers.append(item)
    return tuple(markers)
