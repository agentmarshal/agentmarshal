+++
schema = 1
id = "CR-139"
title = "ADR-0019: accounting — time, quota resets, money"
scope = [
  "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
]
acceptance = [
  "ADR-0019 renders the decision the operator approved (revision 2 of the draft, with the operator's decisions at its end) faithfully and completely: a session's start and end recorded explicitly, its write time unchanged; lead time and its phases in report, unknown for older sessions rather than substituted; the provider's quota-reset time on a provider-limit session; an optional cost with amount, currency and source, apart from tokens, summed per currency without conversion; the outcome values documented (the field already accepts any non-empty string); idempotent cost recording after completion; the session summary in the journal and raw provider exports in the process log; the journal-transaction cost sentence as documentation; the capture classes economics and sessions left outside this decision — no point dropped and none added",
  "the ADR has the form of ADR-0012..0017 including Consequences and Alternatives considered, derived from the decision without adding decision points; it builds on ADR-0004, ADR-0005, ADR-0014 and ADR-0015, and answers proposals 018 (cost), 024 (reset time), 026 (third finding), 032 and 034 (the output-limit value)",
  "every statement about present behaviour matches the file it rests on — what a session record carries today (role, actor, activity, outcome, tokens, usage), that its created_at is the write time and sessions are often written after completion, that outcome accepts any non-empty string, that provider-limit is a documented value",
  "proposals are referred to as 'proposal NNN' and linked; earlier ADRs are named and linked; the record model is a later decision without a number; nothing names a private document, an adopter, a client or an unpublished release",
  "the full CI sequence passes",
]
+++

# CR-139: ADR-0019 in English

## Context

The operator approved the accounting decision in Russian on 2026-10-03, after
a cross-check: sessions get explicit start and end times, report shows lead
time by phase, a provider-limit session can carry the reset time, and cost
can be recorded in a currency apart from tokens.

## Objective

ADR-0019 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing anything the ADR decides.
- The documentation map line.
