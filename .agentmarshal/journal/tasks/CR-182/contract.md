+++
schema = 2
id = "CR-182"
title = "review and submit-review take the reviewer's declared actor and write it into the review record"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/submit_review.py",
  "tests/",
  "openspec/changes/reviewer-actor-flag/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change reviewer-actor-flag has a proposal, a design.md and a delta spec on the capability review-evidence with ADDED requirements for the flag; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal submit-review` and `agentmarshal review` (the launcher, including its finding-review form) take an optional `--actor <id>`; when given, the review record's `reviewer` object carries `actor` with that value, through `create_review_record`'s existing parameter; the record is then schema 7 by the minimum-schema derivation",
  "without `--actor` the record, its schema stamp and every line the commands print are exactly as before — a test pins that a review written without the flag is byte-for-byte the record the previous release wrote, apart from its id and times",
  "an `--actor` value the record rules refuse (empty, all whitespace, a character that could forge a line) is refused before anything is written or the reviewer is launched, naming the flag; an id that is not in the project's actors table is accepted and the command says it is not a declared actor; `--dry-run` of the launcher shows the actor it would record",
  "the reviewer actor is not confused with `recorded_by`: a test shows a review whose recorder and reviewer actor differ keeps both; no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/"]
decisions = ["ADR-0018", "ADR-0022"]
+++

# The reviewer's declared actor on the record

## Context

ADR-0018 decision 3 lets a contract name its permitted reviewers and an
independence rule `distinct-actor`; ADR-0022 sections 2 and 5 give the
review record `reviewer.actor` — the id of the declared reviewer actor —
for the gate to compare. CR-174 landed the key in the record model and
`create_review_record` accepts it, but neither command that writes a review
can set it, so every review lacks it and the gate checks that follow
(membership in `reviewers`, `distinct-actor`) would have nothing to read.

`recorded_by` says who wrote the record; `reviewer` says who is said to
have reviewed. The actor goes into the second; the first is stamped by the
writer as before.

## Objective

A review can name the declared actor that performed it.

## Acceptance Criteria

As in the header.

## Non-Goals

- The gate checks that read the actor (membership in the contract's
  `reviewers`, the `distinct-actor` rule) and `status` showing it (later
  tasks).
- Deriving the actor from the environment or the git identity: the flag is
  explicit, because the process that launches a reviewer is usually not the
  reviewer.
- `previous_review` and `classes` (a later task in the same module).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
