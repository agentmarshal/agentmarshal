# CR-005: ADR-0004 — journal data model

Owner: lead
Type: docs
Priority: P1
Created: 2026-07-19
Status: done
Completion-Review: CR-005
Reviewed-Commit: 0aa372c183637c055a1a80d1e217b8e2cb9588a8
Target-Branch: master
Merged-Commit: b8e08f6c96ebc16dde25474bdde7c1d87e7d701e
Completed-At: 2026-07-19T03:12:41Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-005-completion-0aa372c18363.md
Completion-Review-SHA256: sha256:f9ec8f5a3badcf04b2552f1c2c367891f9e2e75ebe1c0f54877c738f577d289a
Scope:
- .agentmarshal/journal/tasks/open/CR-005-adr-0004-journal-model.md
- docs/adr/

## Context

The journal is the center of the product; its data model is the most
consequential open design decision and gates all schema and CLI work.
The decision was reviewed with the lead before this task was opened;
this task records it as ADR-0004.

## Objective

`docs/adr/ADR-0004-journal-data-model.md` records the journal data
model, self-contained and public-safe.

## Acceptance Criteria

- [ ] The ADR fixes the hybrid model: contracts are human-authored
      markdown documents with a machine-readable TOML header; all
      evidence (reviews, verdicts, completion, lifecycle events,
      execution-input snapshots, measurements) is append-only JSON
      records written exactly once by trusted recorders, with
      collision-free record paths.
- [ ] Task state is a deterministic projection of records, never a
      mutable field; no materialized state files are committed.
- [ ] Gates never parse prose; the JSON record is the machine source of
      truth; validation is fail-closed, stdlib-only, schema-versioned,
      and rejects internally inconsistent records.
- [ ] Execution-input snapshots are captured by the launcher at launch
      time, content-addressed, one per used version.
- [ ] Storage sits behind a single I/O seam (recorder write, loader
      read/projection); git-tracked files are the only shipped backend;
      a derived database index is named as the sanctioned escalation;
      the repository remains the permanent source of truth.
- [ ] Records carry a visibility class: public records in the
      repository, private records in a persistent local store outside
      git, public records may reference private content by hash; full
      session transcripts never enter the public store and require a
      double opt-in for the private one.
- [ ] The ADR addresses why an external database as source of truth is
      rejected despite the known industry precedent of a git-native
      task tracker migrating to one, follows the structure of
      ADR-0001..0003 and cross-references them.

## Non-Goals

- No field-level schemas, no migration tooling, no signing — follow-up
  tasks.
- No implementation.
