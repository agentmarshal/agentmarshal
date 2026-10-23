+++
schema = 2
id = "CR-198"
title = "Documentation: the quickstart describes what status prints in 0.5.0, and ADR-0015 says the gate's check of added records is the write side"
scope = [
  "docs/quickstart.md",
  "docs/adr/ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md",
]
acceptance = [
  "docs/quickstart.md describes, where it describes `status`, every part of the per-task view a 0.5.0 build prints that it does not describe yet — the overdue-step lines on stdout and the paths on stderr (CR-162), the schema-7 record lines and the no-agreement line (CR-184), the declared assignment (CR-191), the changes_required count and the deferred dispositions (CR-194) — each checked against src/agentmarshal/journal/status_view.py and what the command prints, with nothing described that the code does not print",
  "ADR-0015 carries a dated clarification: the gate's validation of the records a candidate adds is the write side of decision 1 — the author can still fix them — so every current rule applies to them whatever schema they declare; the clarification names the finding that showed it (CR-145, review round 1) and changes nothing else in the decision",
  "no other document changes; every link added resolves; the suite and the full CI sequence pass",
]
documents = [
  "docs/quickstart.md",
  "docs/adr/ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md",
]
decisions = ["ADR-0015", "ADR-0016", "ADR-0018", "ADR-0022"]
+++

# Documentation: status in 0.5.0, ADR-0015

## Context

Two documentation debts recorded during 0.5.0 work:

- `status` gained parts of its per-task view in CR-162, CR-184, CR-191 and
  CR-194; the quickstart describes none of them (a review of CR-162 raised
  it in both runs).
- In CR-145 the coordinator first placed the gate's check of records a
  candidate adds on the read side of ADR-0015; the review showed that this
  let a forged record with a lowered schema through. The landed rule treats
  added records as the write side; ADR-0015 does not say so.

## Objective

A reader of these documents learns what is true today.

## Acceptance Criteria

As in the header.

## Non-Goals

- Release notes and UPGRADING (the release documentation task).
- Moving requirements between OpenSpec capabilities; a procedure for
  updating a capability's Purpose (separate process work).
- Proposal 041–043 dispositions: under the operator's review of the queue model, not to be edited before that decision.
- Cosmetic edits beyond the two debts.
