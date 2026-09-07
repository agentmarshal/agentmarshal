+++
schema = 2
id = "CR-093"
title = "The gate sees both ends of a rename: scope, lane and emptiness read one listing"
scope = [
  "src/agentmarshal/journal/gate.py",
  "tests/test_gate.py",
  "openspec/changes/close-rename-scope-hole/",
  "openspec/changes/archive/",
  "openspec/specs/scope-enforcement/",
]
acceptance = [
  "every scenario in openspec/changes/close-rename-scope-hole/specs/scope-enforcement/spec.md is demonstrated by a test whose docstring names it, and each such test fails when the scope check reads git diff --name-only again; the implementation follows design.md's decisions or records in design.md why it departed",
  "the gate reads a candidate's paths from one listing: the name-only helper is gone, and a rename's source counts as a deleted path for the scope check, the lane choice and the empty-range refusal",
  "the byte-for-byte 0.3.0 transcript test and the sidecar transcript tests pass unmodified; no PASS wording changes",
  "the change is archived in the same candidate: openspec/specs/scope-enforcement/spec.md exists with a written Purpose, openspec/changes/archive/ holds the change, and openspec validate --all passes",
  "tasks.md's checkboxes are ticked for the work that landed",
]
decisions = ["ADR-0010"]
documents = ["openspec/changes/close-rename-scope-hole/"]
+++

# CR-093: the gate sees both ends of a rename

## Context

The gate lists a candidate's changed paths two ways: by name only for the
scope check, the lane choice and the empty-range refusal, and by status —
a rename decomposed into a deletion and an addition — for the append-only,
validity and collision checks. Git shows a rename by its destination in the
first listing, so a candidate whose scope covers the destination can move a
file out of a place its scope does not cover, and a move into the journal
reads as a journal-only candidate. The first listing is the defect; the
second already states the rule. proposal.md — Why says the same in the
spec's words. A new capability, `scope-enforcement`, records what the gate
holds a candidate's paths to; this is its first requirement.

## Objective

One listing of what a candidate touches, in which a rename is its source
deleted and its destination added, read by every check that reads paths.

## Acceptance Criteria

As in the header. The spec's scenarios are the behaviour; design.md's
decisions are the shape; tasks.md is the checklist the implementer ticks.

## Threat model and boundaries

A candidate that renames a file out of a protected location deletes it
there; the scope check must see the deletion. ADR-0010 reads an extension's
footprint as scope through the same check, so a rename out of a footprint
is refused by the same line. The refusal names the source path as a path
outside scope; no new transcript wording is introduced.

## Non-Goals

- Rename detection settings (`-M` thresholds, copies): git's defaults stand.
- Any change to what scope syntax means or how a contract is read.
- The `base_tree` listing without `-z` and the other gate small items in the
  backlog.
