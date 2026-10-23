+++
schema = 2
id = "CR-197"
title = "A launched review records what the reviewer executed, read and could not run, and the evidence for each finding; the prompt asks for both and for each criterion's place in the diff"
scope = [
  "src/agentmarshal/journal/review.py",
  "docs/quickstart.md",
  "tests/",
  "openspec/changes/review-verification-launcher/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change review-verification-launcher has a proposal, a design.md and a delta spec on the capability review-evidence with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "the verdict protocol admits an optional `verification` object — `executed` (a list of `{what, result}`), `read` (a list of strings), `not_run` (a list of `{what, why}`) — and an optional `evidence` object mapping finding ids to a link, a `file:line` or a command with the essential part of its output; the launcher records them through the fields CR-178 landed; a verdict without them is recorded exactly as before",
  "a malformed `verification` or `evidence` never refuses the verdict: the malformed part is dropped with a warning naming it, an `evidence` entry for an id the verdict does not carry is dropped with a warning, and the rest is recorded — as the launcher treats `classes` since CR-185",
  "the prompt the launcher builds asks for the `verification` section, for evidence per finding, and for each acceptance criterion where the diff meets it and which test demonstrates it (in the prose); it states that a finding about an external fact the reviewer could not check is advisory and marked unconfirmed (ADR-0017 decision 5); docs/quickstart.md's verdict-protocol section states the two keys",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/", "docs/quickstart.md"]
decisions = ["ADR-0017", "ADR-0022"]
+++

# A launched review records what was verified and on what evidence

## Context

ADR-0017 decision 4: the verdict says what the reviewer ran and with what
result, what it checked by reading only, and what it could not run and
why. Decision 5: a finding carries an optional evidence reference, and a
finding about an external fact the reviewer could not check is advisory —
"unconfirmed". ADR-0022 section 2 names `verification` and `evidence`;
CR-178 landed them in the record model; nothing writes them. Reviews in
this repository have approved with no prose at all, leaving the
coordinator to check by hand what was looked at.

## Objective

A review record says what its verdict rests on.

## Acceptance Criteria

As in the header.

## Non-Goals

- Requiring the sections: they stay optional, and a review without them is
  recorded as before.
- `submit-review` flags for these fields; `status` and `report` showing them.
- Verifying what the reviewer says it ran.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
