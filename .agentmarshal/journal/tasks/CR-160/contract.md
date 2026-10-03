+++
schema = 2
id = "CR-160"
title = "A session record of schema 7 may carry the commit it produced, the model, a trace link, a CLI session id, a report-ready flag and a fallback reason"
scope = [
  "src/agentmarshal/journal/records.py",
  "tests/",
  "openspec/changes/session-fields-schema-7/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change session-fields-schema-7 has a proposal, a design.md and a delta spec modifying the session-activity capability (MODIFIED requirements keep their exact headers, ADDED for new ones); every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "a session record may carry, from schema 7 only: `commit` (40 lowercase hex), `model` (a non-empty string), `trace` (a non-empty string — an external link, never fetched), `cli_session` (a non-empty string), `report_ready` (a boolean) and `fallback_reason` (a non-empty string); each is optional; each string field passes the forgeable-text rule registered for exactly that record type and field; ADR-0022 section 8 bounds no length for these fields, so none is bounded",
  "any of these fields on a session below schema 7 is refused at write and, on read, by the field-admission rule of the record's own schema, as the other schema-gated fields are; a writer that carries any of them stamps schema 7 through the minimum-schema derivation, and a session without them stamps what it stamps today (3, or 6 for coordination)",
  "the fields are registered through the CR-154 registry and validator tables — nothing else is touched to add them — and `create_session_record` accepts them as optional keyword arguments",
  "no other record type changes, the gate's fixtures are unchanged, `uv run agentmarshal validate` passes on this repository's journal, and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
+++

# CR-160: session fields of schema 7

## Context

ADR-0022 section 2 adds to the session record: `commit` (ADR-0018 decision
3), `model` (ADR-0018; the vendor stays `usage.provider`), `trace` and a
separate `cli_session` (proposal 042; two fields by the operator's decision
on revision 3), `report_ready` (proposal 041) and an optional
`fallback_reason` (ADR-0018; shown, never verified). CR-154 made schema 7
known with one registry for field families and shared validators. The
times, reset and cost fields are a separate task; the `record-session`
flags that write all of them are another.

## Objective

A session record can say what it produced and with what, under schema 7.

## Acceptance Criteria

As in the header.

## Non-Goals

- `started_at`, `ended_at`, `resets_at`, `cost` (a separate task).
- `record-session` command-line flags (a separate task).
- Any reader of these fields (gate, status, `next`).
