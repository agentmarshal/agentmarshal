+++
schema = 1
id = "CR-144"
title = "Documentation tail after ADR-0022: the activity probes leave the declined stage, the map reaches ADR-0022, four review advisories"
scope = [
  "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
  "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
  "docs/proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md",
  "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md",
  "docs/README.md",
]
acceptance = [
  "proposal 042 no longer leaves the activity-probe extension point on the declined `step` stage: the dated 2026-10-03 disposition says the probes (the paths a run owns, the session id, the process tree) are declared to the supplied watchdog component the harness runs, and the core still knows no CLI; the earlier text stays visible; and the file's sections run Finding, Proposed, the dispositions in date order, then Where, as every other proposal does",
  "ADR-0019's fourth Consequences bullet attributes the outcomes reading the same way in every project to the vocabulary being shared, not to its being unenforced, in a correction listed in the ADR's existing Corrections note",
  "proposal 041 links proposal 036 at each mention its dated text makes and names it 'proposal 036' each time; ADR-0022 links ADR-0017 and ADR-0019 where it first cites each, as it links the other ADRs",
  "the documentation map in docs/README.md has a line for ADR-0022 in the style of the lines for ADR-0016..0021",
  "no decision point is added or removed; nothing names a private document, an adopter, a client or an unpublished release; the full CI sequence passes",
]
+++

# CR-144: documentation tail after ADR-0022

## Context

Reviews of CR-142 and CR-143 approved with advisories: proposal 042 still
declares activity probes at a stage the operator declined, its new
disposition sits after Where, a Consequences sentence in ADR-0019 gives the
wrong cause, two documents cite without links, and ADR-0022 has no map line.

## Objective

The published text is consistent after the record model.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change to code or to other documents.
