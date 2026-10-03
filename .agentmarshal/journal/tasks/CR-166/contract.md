+++
schema = 2
id = "CR-166"
title = "record-session writes the commit a run produced, the model, a trace link, a CLI session id, report-ready and a fallback reason"
scope = [
  "src/agentmarshal/journal/session.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/record-session-schema-7-flags/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change record-session-schema-7-flags has a proposal, a design.md and a delta spec modifying session-activity (ADDED requirements for the flags; MODIFIED with exact headers where one changes); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal record-session` accepts `--commit <rev>`, `--model <name>`, `--trace <link>`, `--cli-session <id>`, `--report-ready` and `--fallback-reason <text>`, each optional, and writes the matching schema-7 session field (CR-160); `--commit` resolves any revision git accepts to its full 40-character id in the repository the work is in — in a sidecar the host — and refuses an unknown revision with a message naming it",
  "a session recorded with any of these flags is stamped schema 7; a session recorded without them is stamped exactly as before (3, or 6 for coordination); values the record rules refuse (an empty or whitespace-only string, a forgeable character) are refused with the record rule's message and no record is written",
  "`--outcome` stays free text, unchanged; every existing record-session behaviour and test is unchanged",
  "the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
+++

# CR-166: record-session flags for the schema-7 session fields

## Context

CR-160 gave the session record its schema-7 fields (ADR-0022 section 2):
the commit the implementer run produced (ADR-0018 decision 3), the model,
an external trace link and a separate CLI session id (proposal 042), the
report-ready flag (proposal 041) and an optional fallback reason (ADR-0018).
The harness records sessions with `record-session`; until it can pass these,
nothing writes them. The time, reset and cost fields are a later pair of
tasks (record fields, then flags).

## Objective

A harness records what a run produced and with what, in one command.

## Acceptance Criteria

As in the header.

## Non-Goals

- `--started-at`, `--ended-at`, `--resets-at`, cost flags, `--if-missing` (later).
- Any reader of these fields.
