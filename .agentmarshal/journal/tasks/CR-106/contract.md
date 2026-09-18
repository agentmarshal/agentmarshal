+++
schema = 2
id = "CR-106"
title = "A session can be recorded as coordination"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/backfill.py",
  "src/agentmarshal/journal/session.py",
  "src/agentmarshal/cli.py",
  "tests/test_session.py",
  "tests/test_backfill.py",
  "tests/test_attestation.py",
  "openspec/changes/coordination-activity/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "every scenario in the change's delta spec is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "the session activity vocabulary is defined once, and backfill.py and the CLI read it rather than keeping their own",
  "a coordination session record carries the newer schema number, and records with the other three activities carry exactly the schema they carried before",
  "no money or price field is added to any record",
]
decisions = ["ADR-0004", "ADR-0005"]
documents = [
  "openspec/specs/session-activity/",
]
+++

# CR-106: a session can be recorded as coordination

## Context

Proposal 018 (adopter batch D): the session vocabulary has implementation,
review and other, and the most expensive role of an agent-driven loop — the
coordinator — fits only `other`; about three quarters of one fully measured
task landed there. This project's own journal files every lead session as
`implementation`, which is also wrong. The disposition accepted the activity
and deferred a money field, because a price in an evidence record asserts
something no reviewer of the record can check.

## Objective

`coordination` joins the vocabulary, defined once, with a schema number that
lets an older reader refuse it legibly.

## Acceptance Criteria

See the `acceptance` field above; scenarios in the delta spec, decisions in
design.md.

## Amended 2026-09-18

`tests/test_attestation.py` joins the scope. `test_unknown_schema_is_rejected`
uses the first unsupported schema number as its fixture — 6 until this task —
and its own docstring says the number moves as the ladder grows while the
refusal is what it pins. This task makes 6 supported, so the fixture moves to 7.
The implementer stopped at the scope boundary and said so, which is the right
behaviour; the scope named the files the change was expected to touch and
missed the one that encodes "the next number up".

## Non-Goals

- A money field (deferred by the disposition, for its stated reason).
- A per-activity breakdown in `report`.
- Rewriting existing records.
