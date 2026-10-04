+++
schema = 2
id = "CR-174"
title = "A review record of schema 7 may name the task's previous review, a class for each finding, and the reviewer's declared actor"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "tests/",
  "openspec/changes/review-links-and-classes/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change review-links-and-classes has a proposal, a design.md and a delta spec adding to review-evidence the three fields (ADDED requirements; MODIFIED with exact headers only where one becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "from schema 7 a `review` record may carry `previous_review` — a record id in the form record ids take (a 26-character Crockford base32 ULID) — and `classes` — an object whose every key is a finding id the same record names in `findings` or `advisory_findings` and whose every value is a non-empty string; a class outside the project's vocabulary is not refused by the record (ADR-0016 decision 3 — mapping it to `other` is the writer's, a later task); each class value and `previous_review` pass the forgeable-text rule registered for exactly this record type and field",
  "from schema 7 the `reviewer` object may carry `actor` — a non-empty string passing the forgeable-text rule — and stays closed to any other key; below schema 7 the object stays exactly `role`, `vendor`, `model`, `email`",
  "a review carrying any of the three below schema 7 is refused at write and on read, and writing one stamps 7; a review carrying none of them is validated and stamped exactly as before; the fields are declared through the registrations the schema-7 record types use, not by a second mechanism; no other record type changes and nothing reads the new fields yet",
  "the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/"]
+++

# The previous-review link, finding classes and the reviewer's actor

## Context

ADR-0022 section 2 adds three fields to the `review` record in schema 7:
`previous_review`, the id of the task's previous review, so a task's
reviews form a chain (ADR-0016 decision 2); `classes`, a class for each
finding from the project's vocabulary, where a class outside it is recorded
as `other` rather than refused (ADR-0016 decision 3); and `actor` inside
the `reviewer` object, the declared reviewer actor the distinct-actor rule
compares (ADR-0018 decision 3). This task gives the record the fields; the
launcher that writes them, the vocabulary mapping, and every reader are
later tasks.

## Objective

The journal can carry a review's link to the previous one, its findings'
classes and its reviewer's declared actor.

## Acceptance Criteria

As in the header.

## Non-Goals

- The `review` launcher writing the fields, mapping a class to `other`
  with a warning, or resolving `previous_review` against the journal; any
  reader — `status`, `report --findings`, the gate's independence rules
  (later tasks).
- Recomputing or backfilling existing review records.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
