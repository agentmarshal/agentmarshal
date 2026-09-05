+++
schema = 1
id = "CR-085"
title = "ADR-0009: a research task lands through findings, not diffs"
scope = ["docs/adr/ADR-0009-research-findings-lifecycle.md"]
acceptance = [
  "the ADR exists at the scoped path, reads Status: Accepted, and states up front that it decides and does not implement",
  "it names the record type, the review binding, and the gate lane, and for the lane lists which checks run and which print as not examined with a reason",
  "it states what a finding plus review establishes and what it does not, in the manner of ADR-0006",
  "it names the schema consequence and how 0.3.0 fails on such a record, and the five registration points a record type touches",
  "it records the alternatives considered and why each was not taken",
  "it changes no code and no other document",
]
+++

# CR-085: ADR-0009

## Context

Two research tasks in our own sidecar journal have their work done and cannot
complete: nothing in the lifecycle can bind a review to a conclusion, only to a
commit. Proposal 005 named the same gap from an adopter's side and was accepted
on 2026-09-01 with the sequencing "shape it during the sidecar dogfood". The
dogfood happened; the shape is in hand. The plan to 0.4.0 puts this ahead of
signing because the sidecar should close research tasks before we start
signing records.

## Objective

Record the decision — a `finding` record pinned by artifact hash, a review that
may bind to it, and a findings lane in the gate admitted by an empty scope — as
ADR-0009, with the claim boundary and the alternatives, so the implementation
task has a contract to be reviewed against.

## Acceptance Criteria

- `docs/adr/ADR-0009-research-findings-lifecycle.md` exists, reads
  `Status: Accepted`, and says in its preamble that the mechanism is not
  implemented by the document.
- It names the three parts — the `finding` record and its required fields, the
  `reviewed_finding` binding as exactly-one-of with `reviewed_commit`, and the
  findings lane — and for the lane lists the checks it computes and the checks
  it prints as not examined, each with its reason.
- It states what a finding and an approving review of it establish and what
  they do not, in the manner of ADR-0006 and ADR-0008 §7.
- It names the schema consequence (a new type and a new field appear only when
  the lane is used; 0.3.0 refuses such a record fail-closed) and the five
  places a record type is registered.
- It records the alternatives considered — direct artifact digest on the
  review, a separate review type, lane chosen by command, leaving research
  tasks unclosable — and why each was not taken.
- The diff touches the one scoped file and nothing else.

## Threat model and boundaries

The hazard is an ADR that reads as shipped behaviour. The preamble states the
boundary the way ADR-0008's does, and the acceptance criteria hold it to that.

The second hazard is a lane that lets a task promising a diff land without
one. The ADR closes it by making the contract, not the command, choose the
lane: a declared scope keeps the diff lane.

Not a defect here: that the lane is not built. That is the next task.

## Non-Goals

- **Any code.** No record type, no gate change, no CLI.
- Updating proposal 005's disposition, `brief`'s wording, or the overview's
  terminology — all follow the implementation, where they can point at what
  exists.
- Deciding the in-toto projection of a finding beyond noting that its subjects
  are the artifact digests; the projection is wave S.
