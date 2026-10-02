+++
schema = 1
id = "CR-137"
title = "ADR-0017: evidence of reviews and checks"
scope = [
  "docs/adr/ADR-0017-evidence-of-reviews-and-checks.md",
]
acceptance = [
  "ADR-0017 renders the decision the operator approved (revision 2 of the draft, with the operator's decisions at its end) faithfully and completely: a record of a check outcome written by whoever observed the run, travelling with the task's next journal transaction and admitted after completion as a measurement; the gate deciding nothing from it; the brief carrying the latest failing check and report counting candidates rejected by checks; the verdict saying what the reviewer ran with what result, what it only read and what it could not run; evidence on a finding and the protocol line for an unverifiable external fact; the snapshot-preparation command left open as its own later decision — no point dropped and none added",
  "the ADR has the form of ADR-0012..0015, builds on ADR-0004, ADR-0005 and ADR-0014, names its revision of the record-lifecycle and gate-lanes specifications (a check record after completion), states the check record's guarantee as declared by the observer, and answers proposals 026 (first finding), 028 and 030",
  "every statement about present behaviour matches the file it rests on — that no record stores whether the pipeline passed, which attestation mode is the default and what each mode trusts, that a failing run leaves nothing, that the review snapshot carries no installed dependencies, which records are admitted after a terminal state",
  "proposals are referred to as 'proposal NNN' and linked; earlier ADRs are named and linked; the record model is a later decision without a number; nothing names a private document, an adopter, a client or an unpublished release",
  "the full CI sequence passes",
]
+++

# CR-137: ADR-0017 in English

## Context

The operator approved the decision on the evidence of reviews and checks in
Russian on 2026-10-03, after a cross-check: a check outcome becomes a record,
the verdict says what was run and what was read, and a finding about an
external fact carries its evidence or is advisory. It answers proposals 026
(first finding), 028 and 030.

## Objective

ADR-0017 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing anything the ADR decides.
- The documentation map line.
