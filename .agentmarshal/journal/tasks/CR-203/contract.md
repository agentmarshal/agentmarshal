+++
schema = 2
id = "CR-203"
title = "The gate checks that the review comes from a reviewer the contract names and that the implementers are ones it names"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/",
  "openspec/changes/gate-assignment-membership/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change gate-assignment-membership has a proposal, a design.md and a delta spec on the capability contract-governance with ADDED requirements (and MODIFIED for the `distinct-actor` comparison CR-186 added); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "for a trusted contract whose header declares `reviewers`, the gate prints one line judging the latest review's `reviewer.actor` against that list by exact string equality: a PASS when it is in the list, a FAIL naming the actor and the list when it is not, and a FAIL when the review carries no `reviewer.actor`, saying the review is recorded with `--actor` (operator decision of 2026-10-23); without a review (`--without-review`) the line reads NOT EXAMINED",
  "for a trusted contract whose header declares `implementers`, the gate prints one line judging the `actor` of every implementer session whose `commit` is in the candidate's range against that list by exact string equality: PASS when all are in it, FAIL naming each that is not; NOT CHECKED, with the reason, when no implementer session carries a commit in the range — a provider's CI run holds no session yet — and that line is neither a refusal nor a pass",
  "`distinct-actor` compares actor ids by exact string equality, as `status` does since CR-191 (the case-folded comparison of CR-186 is replaced); a contract declaring neither list produces today's transcript byte for byte, which the pinned default transcript and the fixtures demonstrate unchanged",
  "values from records and contracts are escaped in the gate's output as its other lines are; no other gate check changes; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
decisions = ["ADR-0006", "ADR-0018", "ADR-0022"]
+++

# The gate checks membership in the declared assignment

## Context

ADR-0018 decision 3: the review that makes a candidate mergeable comes from
a permitted reviewer and satisfies the declared independence rules against
the implementers whose commits the candidate carries; the reason for a
fallback is shown, not verified. ADR-0022 section 5 says "not checked"
where a field a rule needs is absent, but did not settle membership when a
review names no actor. The operator decided on 2026-10-23: the gate
refuses — membership is what the contract claims, and without an actor it
cannot be shown; `review --actor` (CR-182) is the path. CR-186 landed the
independence rules, CR-191 the display of the assignment with exact actor
comparison.

## Objective

A contract that names its reviewers and implementers gets that checked at
the merge boundary.

## Acceptance Criteria

As in the header.

## Non-Goals

- Checking the fallback order or why a later entry ran.
- Verifying that an actor label is who it claims to be (ADR-0006: declared
  labels until signing).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
