+++
schema = 2
id = "CR-167"
title = "A check record of schema 7 records what a pipeline check found on a commit, and is admitted after any terminal record as a measurement"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/status.py",
  "tests/",
  "openspec/changes/check-record/",
  "openspec/changes/archive/",
  "openspec/specs/record-lifecycle/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change check-record has a proposal, a design.md and a delta spec: review-evidence gains the check record (ADDED requirements), and record-lifecycle gains scenarios that a check record is admitted after a completed and after an abandoned task, as a measurement (MODIFIED requirements keep their exact headers); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "a `check` record type exists from schema 7, declared once in the record-type registry with its predicate type, as a measurement admitted after any terminal record, writable, and requiring `recorded_by` with `recorded_by_source`; its fields are `commit` (40 lowercase hex, required), `name` (required), `result` (one of passed, failed, error, skipped; required), and optional `failed_step`, `excerpt` and `run_url`",
  "`excerpt` is bounded at 4 KiB of UTF-8 through the byte-bounded text rule of CR-154 (refused beyond, never truncated by the record layer); `name`, `failed_step`, `excerpt` and `run_url` pass the forgeable-text rule, registered for exactly this record type and field",
  "a check record on a schema below 7 is refused at write and on read; writing one stamps 7; adding the type changes nothing about any other record type, and the projection and the gate admit it after a terminal record through the one registry, with no second list",
  "the gate's fixtures are unchanged, `uv run agentmarshal validate` passes on this repository's journal, and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/", "openspec/specs/record-lifecycle/"]
+++

# CR-167: the check record

## Context

ADR-0017 decision 1 and ADR-0022 section 3: a `check` record traces what a
pipeline check found on a commit — its name, result, the failed step, a
bounded excerpt and a link to the run — written by whoever observed the run;
the gate decides nothing from it. It is a measurement, admitted after any
terminal record, completed or abandoned. The excerpt is leak-scanned at
write; that, the `record-check` command, the gate's wording of the
measurements line and the brief's last failing check are later tasks.

## Objective

The journal can carry the outcome of a pipeline check as a record.

## Acceptance Criteria

As in the header.

## Non-Goals

- The `record-check` command and the leak scan of the excerpt at write (a later task).
- The gate's measurements-only line wording, the brief and report (later tasks).
