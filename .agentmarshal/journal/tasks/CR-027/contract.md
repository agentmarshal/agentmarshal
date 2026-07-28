+++
schema = 1
id = "CR-027"
title = "in-toto attestation fields: schema v2 provenance + predicateType registry"
scope = ["src/agentmarshal/journal/attestation.py", "src/agentmarshal/journal/records.py", "tests/test_attestation.py", "tests/test_journal.py"]
acceptance = []
+++

# CR-027: in-toto attestation fields: schema v2 provenance + predicateType registry

## Context

ADR-0005 (Decision 5) names the fields that keep an in-toto Statement
losslessly derivable from a journal record, and its Decision 1 invariant —
"no capture setting drops the journal below in-toto Statement
completeness" — is explicitly deferred to an activation-boundary slice:
the schema fields plus the `validate` check that enforces them. This is
that slice.

Per the ADR compatibility matrix most Statement inputs are already present
(`subject[].digest` = reviewed/completed commit; `predicate` body =
verdict/reviewer/findings/tokens) or derivable at projection time (the
`predicateType` from the record type; the reviewed contract's hash; the
git writer identities). The one field that is neither present nor
derivable is **provenance** — whether a record was captured live or
imported by a later backfill (ADR-0005 Decision 4). CR-027 adds it, plus
the predicateType registry the projection and the completeness check both
need, without touching the projection itself (wave 2).

## Objective

Introduce record schema version 2 — provenance-carrying and
in-toto-Statement-projectable — as a non-breaking superset of schema 1,
and the predicateType URI registry, so that forward capture writes
in-toto-complete records and the backfill (a later CR) has the fields it
needs. Schema-1 records already in the journal stay valid (grandfathered).

## Acceptance Criteria

- [ ] A new `src/agentmarshal/journal/attestation.py` defines a
      predicateType URI registry mapping every record type
      (`opened`, `review`, `completed`, `abandoned`, `session`) to a
      stable AgentMarshal predicateType URI, with a lookup helper that
      fails closed on an unregistered type, and the allowed provenance
      values (`live`, `imported-from-host`).
- [ ] `records.py` accepts `schema` 1 or 2. A schema-2 record additionally
      requires a `source` field that is one of the registered provenance
      values, and permits an optional `artifacts` field: a list of
      `{ref, hash}` objects (non-empty ref string; hash exactly 64
      lowercase hex characters). A schema-1 record is validated exactly as
      before and must NOT carry `source` or `artifacts`. Every record
      type's `record_type` must be present in the predicateType registry.
- [ ] The unexpected-field check remains fail-closed per schema version:
      `source`/`artifacts` are rejected on schema 1 and any other unknown
      field is rejected on both.
- [ ] The `create_*` record builders are unchanged and keep emitting
      schema 1 (their many call sites — `open_task`, `submit_review`,
      `complete`, `session`, and `migrate` — are out of this slice's
      scope). Flipping forward capture to emit schema 2 is a separate CR;
      CR-027 delivers the schema-2 support and enforcement the flip and the
      backfill depend on.
- [ ] `agentmarshal validate` stays green on the existing journal (schema-1
      history) and rejects a schema-2 record missing/invalid `source` or
      referencing an unregistered predicate type.
- [ ] Tests in `tests/test_attestation.py` cover: registry lookup +
      fail-closed; schema-2 round-trip with `source` and `artifacts`;
      rejection of a schema-2 record without `source`, with a bad
      `source`, with a malformed `artifacts` entry; rejection of a
      schema-1 record carrying `source`/`artifacts`; the `create_*`
      builders default to schema 2 / `source = live`. Existing
      `tests/test_journal.py` is updated only as the schema bump requires.
- [ ] `uv run agentmarshal validate`, pytest, ruff, and mypy stay green.

## Non-Goals

- No in-toto/DSSE/Sigstore projection (wave 2) — CR-027 only stores the
  fields and the registry; it does not emit a Statement.
- No forward-capture flip: the `create_*` builders and their call sites
  keep emitting schema 1 in this slice; making live capture emit schema 2
  (and migration mark `imported-from-host`) is a later, separately-scoped
  CR that touches those call sites together.
- No capture-policy config, no measurements-post-terminal gate/status
  change, no backfill tool — later CRs in the ADR-0005 chain.
- No rewrite or migration of existing schema-1 records; they remain valid
  as-is (append-only, immutable).
- No `contract_hash`/reviewer-identity storage — those are derivable at
  projection time (ADR-0005 matrix) and are not stored.
