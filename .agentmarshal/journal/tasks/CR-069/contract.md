+++
schema = 1
id = "CR-069"
title = "Records written now carry schema 3, so a version mismatch says so"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/journal/backfill.py", "tests/test_journal.py", "docs/adr/ADR-0004-journal-data-model.md"]
acceptance = [
  "every record this version writes carries `schema = 3`",
  "records of schema 1 and 2 keep validating, so existing journals need no migration",
  "the schema-2 field rules apply at schema 3 and above rather than at schema 2 exactly",
  "ADR-0004 records what schema 3 denotes and that the bump exists to make a version mismatch legible",
]
+++

# CR-069: Records written now carry schema 3, so a version mismatch says so

## Context

The published 0.1.0 cannot read a journal this version writes. Measured
directly: a fresh project, a task, an amendment and a session, then
`agentmarshal validate` from a 0.1.0 install:

```
FAIL: CR-001: record has unsupported fields: recorded_by, recorded_by_source
```

It fails on the **first record**, and the reason is a field name. An operator
reading that goes looking for a field; what they need to be told is that the
journal was written by a version they do not have.

The same mismatch, with the record at schema 3, reports:

```
FAIL: CR-001: record has an unknown or missing schema version
```

Which is the truth, and is actionable.

Records already carry a `schema`, and 0.1.0 already refuses one it does not
know. Nothing new is being invented — the field exists for exactly this and has
simply not been used since the fields it guards started changing.

This is worth doing **now** rather than later. Every adopter is ours today and a
coordinated upgrade costs one pass over the installations; once that stops being
true, a format change costs a negotiation with every journal owner. The bump is
cheap while the window is open and impossible to backfill once it closes.

## Objective

Write schema 3, keep reading 1 and 2, and say in ADR-0004 what the number means.

## Acceptance Criteria

- Every record this version writes carries `schema = 3`, including records
  written by backfill.
- Records at schema 1 and 2 keep validating unchanged, so existing journals
  need no migration and nothing has to be rewritten.
- The rules introduced at schema 2 apply at **schema 2 and above**, not at
  schema 2 exactly.
- ADR-0004 states what schema 3 denotes and why the bump exists.

## Threat model and boundaries

No adversary. This changes a constant and a comparison in code that runs on the
operator's own journal.

The property that must not break is **backward reading**: a journal written
before this change must still validate, or the bump would cost exactly what it
is meant to save. That is an acceptance criterion rather than a guard, and it is
demonstrable by writing records at each schema and validating them.

Nothing here can be attacked: a record claiming a schema we do not support is
already refused fail-closed, which is the behaviour being made use of, not
weakened.

## Non-Goals

- **Migrating existing records.** They stay at the schema they were written at.
  Rewriting history to change a version number would defeat append-only
  evidence for a cosmetic gain.
- Changing any field, any record type, or any validation rule other than the
  version they are gated on.
- Making the old version's message better. 0.1.0 is published and cannot be
  changed; this works forward only.
- A compatibility mode that writes older records. Considered and rejected: it
  would mean a period where the honest attribution `recorded_by` provides is
  silently absent, which is a worse trade for a project whose product is
  evidence.
