"""The one registry of journal record types, and the in-toto vocabulary.

ADR-0005 keeps the flat journal records the source of truth and treats an
in-toto Statement as a *derived projection* (wave 2). This module declares
each record type once — ``RECORD_TYPES`` — giving everything the other
journal modules read about a type:

* the **predicateType** a projected in-toto Statement would carry — a
  stable URI naming the AgentMarshal predicate;
* the task **state** the record projects to, and the terminal states after
  which the type is still admitted (``status.py``'s projection);
* whether a writer may **write** it through the record guard; and
* whether it must name its **recorder** — ``recorded_by`` with
  ``recorded_by_source``;

plus the allowed **provenance** values distinguishing a record captured
live from one imported by a later backfill (ADR-0005 Decision 4).

The registry lives here because this is the module both `records.py` and
`status.py` import; placing it in either of those would make the other
depend backwards. This module owns the declaration; it emits no Statement.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecordTypeSpec:
    """What one record type is, declared once (ADR-0022).

    ``predicate_type`` is the URI a projected Statement would carry;
    ``projects_to`` the task state the record projects to — ``None`` for
    measurements and other non-lifecycle records;
    ``admitted_after_terminal`` the terminal states after which a record
    of the type is still admitted (empty means never — a reopening
    follows completion only, because it returns that state to open);
    ``writable`` whether a writer may create it through the record guard;
    ``requires_recorded_by`` whether the record must name its recorder.
    """

    predicate_type: str
    projects_to: str | None
    admitted_after_terminal: frozenset[str] = field(default_factory=frozenset)
    writable: bool = True
    requires_recorded_by: bool = False


# The one declaration of every record type (ADR-0022). What a module knows
# about a type it reads here: `records.py` reads `requires_recorded_by` and
# `writable`, `status.py` derives its projection tables, and
# `PREDICATE_TYPES` below is the predicate view. Two hand-written places
# still name the types and a new type touches them too — `records.py`'s
# `_RECORD_FIELDS`, the fields the type may carry, without which the
# record-type rule refuses it, and `status.py`'s `WritableRecordType`
# `Literal`, which mypy cannot derive — and a test pins each equal to the
# registry, so a registration that stops here fails loudly, not silently.
# The predicate URIs are part of the interoperability contract — treat them
# as append-only: never repurpose an existing URI. The `/v1` suffix
# versions the predicate shape independently of the record schema.
RECORD_TYPES: dict[str, RecordTypeSpec] = {
    "opened": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/opening/v1", "open"
    ),
    "review": RecordTypeSpec("https://agentmarshal.dev/attestations/review/v1", None),
    "acceptance": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/acceptance/v1", None
    ),
    "completed": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/completion/v1", "done"
    ),
    "abandoned": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/abandonment/v1", "abandoned"
    ),
    "reopened": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/reopening/v1",
        "open",
        admitted_after_terminal=frozenset({"done"}),
    ),
    "amendment": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/amendment/v1", None
    ),
    "session": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/session/v1",
        None,
        admitted_after_terminal=frozenset({"done", "abandoned"}),
    ),
    "finding": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/finding/v1",
        None,
        requires_recorded_by=True,
    ),
    "check": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/check/v1",
        None,
        admitted_after_terminal=frozenset({"done", "abandoned"}),
        requires_recorded_by=True,
    ),
    "agreement": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/agreement/v1",
        None,
        requires_recorded_by=True,
    ),
    "acknowledgement": RecordTypeSpec(
        "https://agentmarshal.dev/attestations/acknowledgement/v1",
        None,
        requires_recorded_by=True,
    ),
}

# The predicate view of the registry: stable URIs naming AgentMarshal's own
# predicate for each record type, kept under the name the vocabulary has
# always exported.
PREDICATE_TYPES: dict[str, str] = {
    record_type: spec.predicate_type for record_type, spec in RECORD_TYPES.items()
}

# Provenance of a record's evidence (ADR-0005 Decision 4): "live" is
# captured at the moment of the event; "imported-from-host" is backfilled
# from retained host data and is provenance-weaker. Verifiers must be able
# to tell them apart, so provenance is stored, not derived.
SOURCE_LIVE = "live"
SOURCE_IMPORTED = "imported-from-host"
SOURCE_VALUES: frozenset[str] = frozenset({SOURCE_LIVE, SOURCE_IMPORTED})


class UnknownPredicateTypeError(KeyError):
    """Raised when a record type has no registered predicateType."""


def predicate_type_for(record_type: str) -> str:
    """Return the predicateType URI for *record_type*, failing closed.

    A record type absent from the registry cannot be projected to an
    in-toto Statement, so the completeness check must reject it rather
    than invent a URI.
    """

    try:
        return PREDICATE_TYPES[record_type]
    except KeyError as error:
        raise UnknownPredicateTypeError(
            f"record type {record_type!r} has no registered predicateType"
        ) from error


def is_registered_record_type(record_type: str) -> bool:
    """Return whether *record_type* has a registered predicateType."""

    return record_type in PREDICATE_TYPES
