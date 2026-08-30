+++
schema = 1
id = "CR-051"
title = "recorded_by: say which actor created a record"
scope = ["src/agentmarshal/journal/actors.py", "src/agentmarshal/journal/records.py", "tests/test_journal.py", "docs/quickstart.md"]
acceptance = [
  "records carry an optional recorded_by naming the actor that created them, plus recorded_by_source saying where that value came from: the project's actors table, the invoking git identity, or an explicit override",
  "the value is derived, not typed: it is resolved from the invoking checkout's git identity, matched against an optional actors table in project.json, with AGENTMARSHAL_ACTOR overriding and marking itself as an override",
  "when no identity can be determined the fields are omitted rather than guessed, and the record stays valid",
  "the fields are optional on schema 2, so every record written before this task remains valid and no migration is needed",
  "stamping happens in write_record, the single point every record passes through, so no record type is left out and no caller changes",
  "docs/quickstart.md documents the actors table and the override",
  "validate/pytest/ruff/format/mypy stay green, with tests for the actors-table match, the git-identity fallback, the override, and the undeterminable case",
]
+++

# CR-051: recorded_by: say which actor created a record

## Context

ADR-0006 decided that identity in the journal is declared, never authenticated,
and that records must separate two claims currently conflated: who is *said* to
have reviewed, and who *created the record*. This project demonstrated the cost
of conflating them — six review records marked `vendor: human` under an
operator's address were produced by an agent, and nothing in the evidence said
so.

It is also the prerequisite for the two-operator question the ADR settles: with
one operator, "who wrote this record" is implicit; with two it is lost.

`recorded_by` does not prevent a false attribution — it is a declaration like
every other identity field, and the ADR says so. What it does is make the honest
case expressible: when an agent records a human's verdict, the record now says
so instead of being silent, and a false attribution needs a second explicit lie.

## Objective

Record which actor created each record, derived from the environment rather than
typed by the caller, without changing what any existing record means.

## Acceptance Criteria

- [ ] Optional `recorded_by` + `recorded_by_source` (actors table / git identity
      / override).
- [ ] Derived from git identity, matched against an optional `actors` table;
      `AGENTMARSHAL_ACTOR` overrides and is marked as such.
- [ ] Omitted, not guessed, when no identity is determinable.
- [ ] Optional on schema 2 — existing records stay valid, no migration.
- [ ] Stamped in `write_record`, so no record type is missed and no caller changes.
- [ ] Documented in `docs/quickstart.md`.
- [ ] Suite green, with the four cases covered.

## Non-Goals

- Not authentication. The field is a declaration, exactly like `vendor` and
  `email`, and the documentation must not suggest otherwise.
- Not policy: distinct-actor review, override authority and end-to-end limits
  are opt-in configuration decided by ADR-0006 and built separately.
- Not role-to-scope permissions (adopter proposal 003), which ADR-0006 places
  after signing.
