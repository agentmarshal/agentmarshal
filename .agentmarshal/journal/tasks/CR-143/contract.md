+++
schema = 1
id = "CR-143"
title = "ADR-0022: the 0.5.0 record model, one transition"
scope = [
  "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
]
acceptance = [
  "ADR-0022 renders the approved decision (revision 2 with revision 3's corrections and the operator's decisions on its seven questions) faithfully and completely, no point dropped and none added: one record schema 7, contract header schema 3, extension manifest schema 2; writers still write the minimum schema they need, yet the transition is immediate because every opened and amendment record carries the contract hash; what a 0.4.x installation does with each (status listing and report fail outright, validate and the gate fail on every task and pull request carrying a schema-7 record, a contract header of schema 3 is refused, a directory-form or schema-2 manifest is unreadable only for an extension the contract names, unknown project.json keys are ignored); the upgrade rule — every clone and CI on 0.5.0 before the first 0.5.0 record, as in 0.4.0",
  "the new fields and record types are those of the approved tables with revision 3's corrections: `actor` permitted inside the closed `reviewer` object, and distinct-vendor and distinct-model comparing the review's reviewer vendor and model with the implementer session; a reason required only for deferred and rejected advisory dispositions, follow-up only on deferred; acceptance of an extension pause bound by the existing accepted commit with no findings required, and acceptance of an operational CR with no review; the session's commit (ADR-0018), started and ended times, reset time, cost, report-ready, `trace` and a separate `cli_session` for resume, an optional `fallback_reason`; the vendor read from the optional `usage.provider`, so a missing one reads 'not checked'; `check` admitted after any terminal record, `ext` with a required commit as ADR-0013 lists, `acknowledgement` with the file as the scan prints it and self-acknowledgement derived on display; `recorded_by` together with `recorded_by_source` required on check, agreement, acknowledgement and ext, a recorder that is not a declared actor accepted and shown as such, distinct-actor then 'not checked'; the resolution-only review mode introduced here with proposal 043 as its source, its metric counting those reviews; the contract header's implementers, reviewers and independence rules; the project.json keys; the limits on new fields only",
  "the local formats are as approved: the process log's line format and events — step started (with step id, kind of work, process and its start time, deadline, optional actor and run directory) and step ended (with outcome), full check output, raw provider exports, review prose and diagnostics, extension events including post-gate results, heartbeats written by extensions and supplied components only, trust changes; the step commands, with `step end` an optional addition while a step is still closed by the record it ends with; the plan file, the trust file and the switch files; the core starts no background process and the watchdog is a supplied component the harness runs",
  "the ADR names every published text it revises — the record-lifecycle requirement on what a terminal task admits, the gate-lanes byte-for-byte requirement and the gate line about session records accruing after a terminal record, ADR-0014 decision 9 on how a step closes, and proposal 042's `step` stage form — and every statement about present behaviour (current schema maxima and who writes them, contract schema 2's three fields, manifest schema 1, how a reader treats an unknown schema, the record file name pattern, `usage.provider`) matches the file it rests on; the ADR has the form of ADR-0012..0021 with Context, Decision, Left open, Consequences and Alternatives considered, derived from the decision",
  "nothing names a private document, an adopter, a client or an unpublished release; the full CI sequence passes",
]
+++

# CR-143: ADR-0022 in English

## Context

ADR-0015..0021 decided what is recorded; this decision gives the record
model that carries it — schema numbers, field names, new record types and
the local formats — and the one coordinated transition to it. The operator
approved revision 2 on 2026-10-03 and, after a cross-check against
everything published, revision 3's corrections and seven recommendations.

## Objective

ADR-0022 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing the schema, the fields, the types, the commands or the formats.
- Editing ADR-0014, proposal 042 or any other published text (a separate task
  amends them; this ADR names the revisions).
- The documentation map line.
