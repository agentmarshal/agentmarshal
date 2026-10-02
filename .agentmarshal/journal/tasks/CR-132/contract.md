+++
schema = 1
id = "CR-132"
title = "ADR-0014: where things live — the journal, the process log, CI output"
scope = [
  "docs/adr/ADR-0014-where-things-live.md",
  "docs/README.md",
]
acceptance = [
  "ADR-0014 renders the decision the operator approved (third revision) faithfully and completely: the three places and what each holds; the process log as a local working log and not ADR-0004/0005's durable private store, with nothing written to the journal at the `hash` level; the gate reading nothing local; the location in the git common directory, and in a sidecar the journal repository's; format, rotation, what the log does not promise; steps in progress; post-gate results; what goes in first; the map of locations with its three rules for the top-level documentation; doctor and status printing actual paths as a new obligation; consequences and alternatives — no point dropped and none added",
  "the ADR has the form of ADR-0011..0013, builds on ADR-0004, ADR-0005, ADR-0008 and ADR-0013, and says plainly that ADR-0005's durable private store stays designed and unbuilt and that ADR-0008's rule on references to private content is unchanged",
  "every statement about present behaviour matches the file it rests on — what the `hash` capture level does today (review.py, the review-evidence spec), that the host is never written in a sidecar (ADR-0008, docs/sidecar.md), what status prints about placement, where the gate reads configuration from — and every path on the map matches ADR-0013 as published (the switches file at .agentmarshal/switches.toml)",
  "proposals are referred to as 'proposal NNN' and linked; ADRs are named and linked; nothing names a private document, an adopter, a client or an unpublished release",
  "the documentation map has a line for ADR-0014, and the full CI sequence passes",
]
+++

# CR-132: ADR-0014 in English

## Context

The operator approved ADR-0014 in Russian (third revision, 2026-10-03) after
a cross-check against the published decisions changed two points: in a
sidecar, local state lives in the journal repository's git directory, because
ADR-0008 promises the host is never written; and the process log is a local
working log, not ADR-0004/0005's durable private store, so nothing is pinned
from the journal into it.

## Objective

ADR-0014 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing the process log, the map in the README, or the path printing.
- Amending ADR-0012 or ADR-0013 (a separate task).
