+++
schema = 2
id = "CR-192"
title = "complete takes a disposition for each advisory finding of the review the gate passed on, and refuses before writing completed when one is missing"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/complete.py",
  "docs/quickstart.md",
  "tests/",
  "openspec/changes/complete-advisory-dispositions/",
  "openspec/changes/archive/",
  "openspec/specs/finding-lifecycle/",
]
acceptance = [
  "the change complete-advisory-dispositions has a proposal, a design.md and a delta spec on the capability finding-lifecycle with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal complete` takes repeatable `--disposition <id>=fixed`, `--disposition <id>=deferred:<reason>` and `--disposition <id>=rejected:<reason>` — the reason is everything after the first colon, so a reason may contain colons — and repeatable `--follow-up <id>=<task>` for a deferred finding; the dispositions are written into the `completed` record's `advisory_dispositions` through `create_completed_record`'s existing parameter",
  "for the review the gate passed on — the approving review, or the non-approving review an acceptance covered — `complete` refuses before writing `completed` when any of that review's advisory findings has no disposition, naming every finding that lacks one; it also refuses, naming the id, a disposition for an id that is not an advisory finding of that review, a `deferred` or `rejected` without a reason, a follow-up on a disposition other than `deferred`, and a value the record rules refuse — and on every refusal writes nothing",
  "a review with no advisory findings completes exactly as today with no flag; `complete --findings` takes no dispositions and gains no refusal (ADR-0016 decision 1); docs/quickstart.md says that `complete` asks for a disposition per advisory finding, with the flag syntax",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/finding-lifecycle/", "docs/quickstart.md"]
decisions = ["ADR-0007", "ADR-0016", "ADR-0022"]
+++

# complete records a disposition for each advisory finding

## Context

ADR-0016 decision 1: for the review the gate passed on, `complete` takes a
disposition for each of its advisory findings — `fixed`, `deferred` with a
reason and optionally a follow-up task, `rejected` with a reason — and
refuses before writing `completed` when any lacks one; the findings lane is
untouched. It adds to ADR-0007: an advisory still blocks nothing, but
silence is replaced by a recorded choice. ADR-0022 section 2 names the
field; CR-175 landed it and `create_completed_record` accepts it. Until now
the coordinator has written these choices into commit messages, because the
command had no way to take them.

## Objective

Every advisory finding of a landed review ends in a recorded choice.

## Acceptance Criteria

As in the header.

## Non-Goals

- `status` and `report` showing open deferrals (later tasks).
- A review-by date on a deferral (pending an operator decision).
- Changing what the gate checks.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
