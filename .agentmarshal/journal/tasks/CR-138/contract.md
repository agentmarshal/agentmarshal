+++
schema = 1
id = "CR-138"
title = "ADR-0018: governing the contract"
scope = [
  "docs/adr/ADR-0018-governing-the-contract.md",
]
acceptance = [
  "ADR-0018 renders the decision the operator approved (revision 2 of the draft, with the operator's decisions at its end) faithfully and completely: the contract's hash in the opening and every amendment, named as a revision of ADR-0005 with its reason; an agreement record by any declared actor, not required by default, its absence visible, requirable by a project, with no roles until signing; the contract header naming permitted implementers and reviewers and independence rules, the gate checking membership and the rules but not the reason for a fallback, status showing declared next to actual, the guarantee declared and cross-checked; contract review before implementation not done, withdrawn by its reporter — no point dropped and none added",
  "the ADR has the form of ADR-0012..0016 including Consequences and Alternatives considered, derived from the decision without adding decision points; it builds on ADR-0005, ADR-0006 and ADR-0015, names its revision of ADR-0005, and answers proposals 031, 033 and 034",
  "every statement about present behaviour matches the file it rests on — that only a launched review carries the contract's hash, that independence today compares the reviewer's address with the candidate's authors and committers, that actors carry no roles, that ADR-0006's distinct-actor policy is designed and off",
  "proposals are referred to as 'proposal NNN' and linked; earlier ADRs are named and linked; the record model is a later decision without a number; nothing names a private document, an adopter, a client or an unpublished release",
  "the full CI sequence passes",
]
+++

# CR-138: ADR-0018 in English

## Context

The operator approved the decision on governing the contract in Russian on
2026-10-03, after a cross-check: the contract's hash is pinned where it is
written, an agreement can be recorded, and the contract may name who
implements and who reviews, with independence rules the gate checks. It
answers proposals 031, 033 and 034.

## Objective

ADR-0018 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing anything the ADR decides.
- The documentation map line.
