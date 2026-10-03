+++
schema = 2
id = "CR-170"
title = "An acknowledgement record of schema 7 records that a leak-scan hit on a commit was reviewed and is not a leak"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/status.py",
  "tests/",
  "openspec/changes/acknowledgement-record/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "the change acknowledgement-record has a proposal, a design.md and a delta spec adding to leak-scan the acknowledgement record (ADDED requirements; MODIFIED with exact headers only where one becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "an `acknowledgement` record type exists from schema 7, declared once in the record-type registry (predicate type, projected state, writable, not admitted after a terminal record, `recorded_by` with `recorded_by_source` required); its fields are `commit` (40 lowercase hex), `file` (the path as the leak scan prints it — masked; non-empty), exactly one of `signature` (a built-in signature id the scan knows) or `marker` (an integer of at least 1, the marker's position), and `reason` (non-empty, at most 1000 characters)",
  "`file` and `reason` pass the forgeable-text rule registered for exactly this record type and field; `reason`'s bound uses the character-bounded rule; a record carrying both or neither of `signature` and `marker` is refused with a message naming them",
  "the record below schema 7 is refused at write and on read; writing one stamps 7; no other record type changes; nothing reads acknowledgements yet",
  "the gate's fixtures are unchanged, the suite passes also with `env -u AGENTMARSHAL_ACTOR`, and the full CI sequence passes",
]
documents = ["openspec/specs/leak-scan/"]
+++

# CR-170: the acknowledgement record

## Context

ADR-0021 and ADR-0022 section 3: an acknowledged leak-scan hit is a record
of its own — bound to the candidate commit, naming the file as the scan
prints it (so the record cannot carry a marker's value) and the hit's
identification (a signature id or a marker's number), with a reason; any
declared actor may write it; self-acknowledgement is derived on display.
The command that writes it and the leak scan and gate marking acknowledged
hits are later tasks.

## Objective

The journal can carry a reviewed leak-scan hit as a record.

## Acceptance Criteria

As in the header.

## Non-Goals

- The `acknowledge` command, the leak scan and the gate reading acknowledgements (later tasks).
- How self-acknowledgement is shown (later, with the readers).
