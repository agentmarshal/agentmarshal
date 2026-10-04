+++
schema = 2
id = "CR-176"
title = "A session record of schema 7 may carry its start and end, the provider's reset time on a provider-limit session, and a cost"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "tests/",
  "openspec/changes/session-times-and-cost/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change session-times-and-cost has a proposal, a design.md and a delta spec modifying session-activity (ADDED requirements for the fields; MODIFIED with exact headers only where one becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "from schema 7 a `session` record may carry `started_at` and `ended_at` — only together, each a UTC ISO-8601 timestamp by the rule `created_at` follows, `ended_at` not earlier than `started_at` — and `resets_at`, a UTC ISO-8601 timestamp by the same rule, admitted only on a session whose `outcome` is `provider-limit`; `created_at` keeps its meaning (the write time) and is never derived from them",
  "from schema 7 a `session` record may carry `cost` — an object with exactly `amount`, a non-negative decimal written as a string of digits with an optional fractional part (for example `\"0.42\"`, never a JSON number, so a sum is exact), `currency`, three uppercase ASCII letters, and `source`, one of `reported` and `estimated` — each refusal naming the field and the key at fault",
  "a session carrying any of the four fields below schema 7 is refused at write and on read, and writing one stamps 7; a session carrying none is validated and stamped exactly as before; the fields are declared through the registrations the schema-7 session family uses, not by a second mechanism; no other record type changes and nothing reads the fields yet",
  "the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
+++

# Session start and end, the reset time, and cost

## Context

ADR-0019 decides what the journal records about a session's time and
money: its start and end, beside `created_at`, which stays the write time
(decision 1); the provider's stated reset time on a `provider-limit`
session (decision 3); and an optional cost — an amount, a currency and its
source, `reported` or `estimated`, summed per currency and never converted
(decision 4). ADR-0022 section 2 names the fields in schema 7:
`started_at`, `ended_at`, `resets_at`, `cost`. ADR-0019 leaves the amount's
form open; this contract fixes it as a decimal string so `report` can sum
it exactly. The `record-session` flags, `--if-missing`, and the `report`
views are later tasks.

## Objective

The journal can carry when a session ran, when a provider's allowance
resets, and what a session cost.

## Acceptance Criteria

As in the header.

## Non-Goals

- `record-session` flags for the fields, `--if-missing`, and `report`'s
  lead time, phases and cost sums (later tasks).
- Any check that a cost's figure is true, or any conversion between
  currencies (ADR-0019 decision 4).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
