"""in-toto attestation vocabulary for journal records.

ADR-0005 keeps the flat journal records the source of truth and treats an
in-toto Statement as a *derived projection* (wave 2). Two pieces of that
vocabulary are needed before the projection exists, because forward
capture and the completeness check both rely on them:

* the **predicateType** each record type maps to — a stable URI naming the
  AgentMarshal predicate a projected Statement would carry; and
* the allowed **provenance** values distinguishing a record captured live
  from one imported by a later backfill (ADR-0005 Decision 4).

This module owns only that vocabulary; it emits no Statement.
"""

from __future__ import annotations

# Stable URIs naming AgentMarshal's own predicate for each record type. A
# projected in-toto Statement would carry the matching predicateType; the
# `/v1` suffix versions the predicate shape independently of the record
# schema. These strings are part of the interoperability contract — treat
# them as append-only: never repurpose an existing URI.
PREDICATE_TYPES: dict[str, str] = {
    "opened": "https://agentmarshal.dev/attestations/opening/v1",
    "review": "https://agentmarshal.dev/attestations/review/v1",
    "completed": "https://agentmarshal.dev/attestations/completion/v1",
    "abandoned": "https://agentmarshal.dev/attestations/abandonment/v1",
    "session": "https://agentmarshal.dev/attestations/session/v1",
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
