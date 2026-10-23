+++
schema = 2
id = "CR-201"
title = "complete takes the advisory findings from the review the gate passed on, as the gate reports it, not from a second read of the journal"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/complete.py",
  "tests/",
  "openspec/changes/complete-uses-gate-review/",
  "openspec/changes/archive/",
  "openspec/specs/finding-lifecycle/",
]
acceptance = [
  "the change complete-uses-gate-review has a proposal, a design.md and a delta spec on the capability finding-lifecycle (MODIFIED for the requirement CR-192 added that names which review's advisory findings need a disposition); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "the gate's report carries the id of the review it passed on — the latest review of the resolved commit, or the review an acceptance covered — or none when it passed on no review; it is set by the same code that decides the verdict check, not recomputed",
  "`complete` takes the advisory findings that need a disposition from the review whose id the gate's report carries, read from the records the gate evaluated; a review appended after the gate ran cannot change which advisory findings are required — a test appends a newer review between the gate and the disposition check and shows the original review's advisory findings still required",
  "the gate's printed transcript is unchanged byte for byte (the id is in the report object, not printed), which the pinned default transcript and the fixtures demonstrate; `complete --findings` is unchanged",
  "no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/finding-lifecycle/"]
decisions = ["ADR-0007", "ADR-0016"]
+++

# complete uses the review the gate passed on

## Context

CR-192's review left an advisory finding, deferred with a follow-up:
`complete` re-reads the latest review after the gate returns, so a review
appended concurrently — by a process of the same user — could replace the
one the gate passed on, and a newer review with no advisory findings could
let completion skip the dispositions of the review that was actually
judged. ADR-0016 decision 1 binds the dispositions to "the review the gate
passed on"; the gate is where that review is decided.

## Objective

The review whose advisory findings need dispositions is the review the
gate judged, by construction.

## Acceptance Criteria

As in the header.

## Non-Goals

- Locking the journal against concurrent writers.
- Any change to what the gate checks or prints.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
