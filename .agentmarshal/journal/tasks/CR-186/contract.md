+++
schema = 2
id = "CR-186"
title = "The gate checks the independence rules a schema-3 contract declares, and says not checked where a rule's field is absent"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
  "openspec/changes/gate-independence-rules/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change gate-independence-rules has a proposal, a design.md and a delta spec on the capability contract-governance with ADDED requirements for the gate's checks; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "for a contract — read from the trusted side, as the gate reads it today — whose header declares `independence`, the gate prints one line per declared rule other than `reviewer-not-writer`, judging the latest review against the implementer sessions of the task whose `commit` is one of the candidate's commits (`merge-base..candidate`): `distinct-vendor` compares `reviewer.vendor` with each such session's `usage.provider`, `distinct-model` compares `reviewer.model` with each session's `model`, `distinct-actor` compares `reviewer.actor` with each session's `actor` where that actor is declared in the project's actors table; a rule holds only if it holds against every such session, and a failing rule refuses the candidate naming the rule and the two values",
  "where a rule cannot be judged — no implementer session carries a `commit` in the candidate's range, a compared field is absent on the review or on a session, or the session's actor is not declared — the line reads NOT CHECKED with the reason, and is neither a refusal nor a pass; when the gate runs without a review (`--without-review`) the rule lines read NOT EXAMINED, as the existing independence line does",
  "`reviewer-not-writer` — the existing check — runs for every candidate exactly as today, whether or not the header names it, and the header naming it adds no second line; a contract that declares no `independence` (every schema-1 and schema-2 contract) produces the gate transcript of today byte for byte, which the pinned default transcript and fixtures demonstrate unchanged",
  "values from records are escaped in the gate's output as the gate's other lines are; no other gate check changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
decisions = ["ADR-0006", "ADR-0018", "ADR-0022"]
+++

# The gate checks the declared independence rules

## Context

ADR-0018 decision 3: the contract may declare the independence rules in
force — the reviewer is not a writer of the candidate (today's check), is a
different declared actor than the implementer, a different vendor, a
different model — and the gate checks them against the implementers whose
commits the candidate carries. ADR-0022 section 5 fixes the vocabulary and
says that where a field a rule needs is absent the line reads "not
checked": not a refusal, and not a silent skip. The fields are on the
record: a session's `commit` and `model` (CR-160, written by
`record-session` since CR-166) and its `usage.provider`; a review's
`reviewer.vendor`, `reviewer.model` and `reviewer.actor` (CR-174, written
by `--actor` since CR-182). CR-147 landed the header field; nothing reads
it yet.

An undeclared actor is a label, not an identity (ADR-0006): comparing two
labels that no actors table vouches for would print a pass or a fail the
journal cannot stand behind, so `distinct-actor` reads "not checked" there,
as ADR-0022 section 3 says.

Membership of the reviewer in the contract's `reviewers` list and of the
implementer in `implementers` is a separate check with an open question
(what to do when the review names no actor), and is not part of this task.

## Objective

A contract that declares independence rules gets them checked at the merge
boundary, and says plainly which could not be.

## Acceptance Criteria

As in the header.

## Non-Goals

- Membership in `reviewers` and `implementers` (a later task, after an
  operator decision).
- `status` showing the declared assignment next to what ran (a later task).
- Verifying that a session's recorded vendor, model or actor is true: the
  guarantee is "declared and cross-checked", not "proven" (ADR-0018).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
