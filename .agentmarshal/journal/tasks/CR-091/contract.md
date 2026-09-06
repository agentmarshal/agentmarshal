+++
schema = 2
id = "CR-091"
title = "Keep the reviewer's prose: a review record pins its output as a journal artifact"
scope = [
  "src/agentmarshal/journal/artifacts.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/submit_review.py",
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/validate.py",
  "src/agentmarshal/journal/status.py",
  "src/agentmarshal/journal/report.py",
  "src/agentmarshal/cli.py",
  "tests/test_artifacts.py",
  "tests/test_review_launcher.py",
  "tests/test_journal.py",
  "tests/test_gate.py",
  "tests/test_validate.py",
  "tests/test_report.py",
  "tests/test_findings.py",
  "docs/quickstart.md",
  "docs/overview.md",
  "openspec/changes/keep-review-prose/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "every scenario in openspec/changes/keep-review-prose/specs/review-evidence/spec.md is demonstrated by a test whose docstring names it, and the implementation follows the decisions in design.md or records in design.md why it departed",
  "a review artifact lives at .agentmarshal/journal/tasks/<task>/artifacts/<record-id>-review.md, is written before the record that cites it, and the record pins it as {ref, hash} with the sha256 of the file's bytes — one helper writes artifacts, and the finding record's artifacts go through the same helper where they are written by this tool",
  "the gate's append-only check reports a modified or deleted file under tasks/<id>/artifacts/ as it reports a record; validate refuses a journal whose pinned review artifact is missing or does not match its hash, naming the record",
  "a journal whose review records carry no artifacts behaves as in 0.3.0: the byte-for-byte gate transcript test and the existing review-launcher tests pass unmodified",
  "the change is archived in the same candidate: openspec/specs/review-evidence/spec.md holds the baseline, openspec/changes/archive/ holds the change, and openspec validate passes on the tree",
  "tasks.md's checkboxes are ticked for the work that landed; the quickstart's review step and the overview's Record entry mention the artifact in one sentence each",
]
decisions = ["ADR-0005", "ADR-0009", "ADR-0010"]
documents = ["openspec/changes/keep-review-prose/", "openspec/specs/review-evidence/"]
+++

# CR-091: keep the reviewer's prose

## Context

The first product task run with a delta spec under the research protocol
(CR-003 in the operator's journal). The spec, proposal, design and task list
live under `openspec/changes/keep-review-prose/` and reach the implementer
through `brief` as named documents; this contract bounds what may change and
what counts as done, and points at the spec for the behaviour rather than
restating it. Motivation: proposal.md — Why.

## Objective

A review record can cite the reviewer's prose as a hash-pinned artifact under
the task's journal directory, on both review paths, held to the record's
immutability and checked by `validate`; a journal that keeps no prose is
unchanged.

## Acceptance Criteria

As in the header. The spec's scenarios are the behaviour; design.md's
decisions are the shape; tasks.md is the checklist the implementer ticks.

## Threat model and boundaries

A pinned hash nobody checks is a field filled in by eye: `validate` checks
it, and the gate holds the file to the record rule. The prose is verbatim
and may contain code excerpts; publication is the journal placement's
decision (ADR-0008) and the leak scan runs over the completion transaction.

## Non-Goals

- A structured findings format; redaction; a capture-policy switch for
  prose; pinning the implementer brief — all named in design.md.
- Backfilling prose for existing records.
- Naming the OpenSpec extension in this contract: the spec paths are listed
  in scope and documents, the route the research protocol chose for product
  tasks.
