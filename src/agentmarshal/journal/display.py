"""Escaping record and contract text for display (ADR-0015 decision 5).

A record is checked at read time by the rules of its own schema, so a value
a later rule would refuse at write can still reach a renderer — written
before the rule existed, or written around the writer with a lowered schema.
Where the tool prints such a value, each refused character is rendered as a
visible escape: it can neither add a line nor reorder what is seen.
"""

from __future__ import annotations

from agentmarshal.journal.records import forges_rendered_text

_NAMED_ESCAPES = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _escape_character(character: str) -> str:
    named = _NAMED_ESCAPES.get(character)
    if named is not None:
        return named
    codepoint = ord(character)
    if codepoint <= 0xFFFF:
        return f"\\u{codepoint:04x}"
    return f"\\U{codepoint:08x}"


def escape_for_display(value: str) -> str:
    """Render each character the forgeable-text rule refuses as a visible escape.

    The characters escaped are exactly those
    :func:`agentmarshal.journal.records.forges_rendered_text` refuses — the
    same predicate the writer consults, so the two sides cannot drift.
    ``\\n``, ``\\r`` and ``\\t`` print by name; every other refused
    character prints as ``\\uXXXX`` (``\\UXXXXXXXX`` past the Basic
    Multilingual Plane). Every character the rule accepts is left as it is.
    """

    if not forges_rendered_text(value):
        return value
    return "".join(
        _escape_character(character) if forges_rendered_text(character) else character
        for character in value
    )
