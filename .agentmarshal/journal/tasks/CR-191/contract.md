+++
schema = 2
id = "CR-191"
title = "status shows a schema-3 contract's declared implementers, reviewers and independence rules next to who actually implemented and reviewed"
scope = [
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "openspec/changes/status-declared-assignment/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change status-declared-assignment has a proposal, a design.md and a delta spec on the capability contract-governance with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "for a task whose contract header declares any of `implementers`, `reviewers`, `independence`, `status <task>` prints an assignment section: the declared implementers and reviewers in their order, and the independence rules in force",
  "next to the declaration the section shows what ran: for each implementer session its `actor`, `model`, the vendor from `usage.provider` and its `fallback_reason` when present; for each review its reviewer's `actor`, `vendor` and `model` — an absent value shown as absent, never guessed; an actor that ran but is not in the declared list is marked as not declared for the role, which is shown, not refused (ADR-0018 decision 3)",
  "a task whose contract declares none of the three fields prints exactly today's detail view, which a test pins byte for byte; every value from a contract or a record is escaped on display",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
decisions = ["ADR-0018", "ADR-0022"]
+++

# status shows the declared assignment next to what ran

## Context

ADR-0018 decision 3: the contract may name the permitted implementers and
reviewers, ordered as the fallback order, and the independence rules in
force; `status` shows the declared assignment next to what actually ran,
and the reason for a fallback is shown, not verified. CR-147 landed the
header fields, CR-160/166 the session's `model`, `commit` and
`fallback_reason`, CR-182 the reviewer's `actor`, CR-186 the gate's check
of the rules. Nothing shows the declaration to a reader yet.

## Objective

A reader of `status` sees who was supposed to do the work and who did.

## Acceptance Criteria

As in the header.

## Non-Goals

- Membership enforcement in the gate (a later task, after an operator
  decision).
- Judging the independence rules in `status`: the gate judges them; `status`
  shows the facts.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
