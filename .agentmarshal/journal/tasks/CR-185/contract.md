+++
schema = 2
id = "CR-185"
title = "A launched review links the task's previous review and records the class of each finding the reviewer names, an unknown class as other"
scope = [
  "src/agentmarshal/journal/review.py",
  "docs/quickstart.md",
  "tests/",
  "openspec/changes/review-links-and-classes-launcher/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change review-links-and-classes-launcher has a proposal, a design.md and a delta spec on the capability review-evidence with ADDED requirements for the launcher; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal review` (both the commit and the finding form) writes `previous_review` — the id of the task's latest review record at launch time, whatever it bound to — when the task has one, and writes no such field when it has none; `submit-review` does not write it",
  "the verdict protocol admits an optional `classes` object mapping finding ids to class strings; the prompt the launcher builds lists the project's vocabulary (`review.finding_classes`, the default when unset) and asks for one class per finding id; the launcher records `classes` for the ids that are among the verdict's `findings` or `advisory_findings`, records a class outside the vocabulary as `other` and prints a warning naming the id and the class given, drops an entry for an id the verdict does not carry with a warning, and never refuses the verdict over a class",
  "a verdict without `classes` is recorded exactly as before — no `classes` field, and the schema stamp rises only for `previous_review`; docs/quickstart.md's verdict-protocol section states the `classes` key and the `other` mapping, and that the launcher links the previous review",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/", "docs/quickstart.md"]
decisions = ["ADR-0016", "ADR-0022"]
+++

# A launched review links and classifies

## Context

ADR-0016 decision 2: a review launched by the `review` command records the
previous review of the same task, so a task's reviews form a chain.
Decision 3: a finding carries a class from the project's vocabulary; a class
outside it is recorded as `other` with a warning — not refused, because a
verdict is the output of a paid run and the class is reference markup no
decision rests on. ADR-0022 section 2 names the fields `previous_review`
and `classes`; CR-174 landed them in the record model and CR-151 the
vocabulary key `review.finding_classes` (read in src/agentmarshal/settings.py).
Nothing writes either field yet.

Showing the reviewer the previous round's findings is a separate mode, off
by default, waiting on the experiment that measures it; this task links
records and does not change what the reviewer is shown.

## Objective

A task's launched reviews can be walked in order, and each finding says
what kind of defect it is.

## Acceptance Criteria

As in the header.

## Non-Goals

- Showing the reviewer previous findings (ADR-0016 decision 2's mode) and
  computing a finding's status against the previous round.
- `submit-review` flags for classes; `report --findings` and `status`
  showing classes (later tasks).
- `verification` and `evidence` from the reviewer (a later task in the same
  module).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
