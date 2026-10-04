+++
schema = 2
id = "CR-175"
title = "A completed record of schema 7 may carry a disposition for each advisory finding of the review the gate passed on"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "tests/",
  "openspec/changes/advisory-dispositions/",
  "openspec/changes/archive/",
  "openspec/specs/finding-lifecycle/",
]
acceptance = [
  "the change advisory-dispositions has a proposal, a design.md and a delta spec creating the capability finding-lifecycle — its Purpose written in the delta, covering ADR-0016's lifecycle of review findings — with ADDED requirements for the field; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "from schema 7 a `completed` record bound by `completed_commit` may carry `advisory_dispositions` — a non-empty object whose every key is a non-empty finding id passing the rule finding ids pass, and whose every value is an object with `disposition` one of `fixed`, `deferred`, `rejected`; `reason`, a non-empty string, required on `deferred` and `rejected` and optional on `fixed`; `follow_up`, a task id in the form task ids take, admitted on `deferred` only; and no other key — each refusal naming the finding id and the key at fault",
  "a `completed` record bound by `completed_finding` carrying `advisory_dispositions` is refused (ADR-0016 decision 1: `complete --findings` takes no dispositions); `reason` and `follow_up` pass the forgeable-text rule, registered for exactly this record type and field through the registrations the schema-7 fields use",
  "a `completed` record carrying the field below schema 7 is refused at write and on read, and writing one stamps 7; a `completed` record without it is validated and stamped exactly as before; no other record type changes and nothing reads the field yet",
  "the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/finding-lifecycle/"]
+++

# Advisory dispositions in the completed record

## Context

ADR-0016 decision 1: for the review the gate passed on, `complete` takes a
disposition for each of that review's advisory findings — `fixed`;
`deferred`, with a reason, optionally naming a follow-up task; `rejected`,
with a reason — and records them in the `completed` record. ADR-0022
section 2 gives the field its shape in schema 7. The findings lane's
`complete --findings` takes no dispositions. This task gives the record the
field; `complete --disposition` and its refusal, and `status`/`report`
showing open deferrals, are later tasks.

## Objective

The journal can carry the recorded choice made for each advisory finding at
completion.

## Acceptance Criteria

As in the header.

## Non-Goals

- `complete --disposition`, the refusal when an advisory finding lacks a
  disposition, and checking the keys against the review's advisory findings
  (they need the journal — later tasks); `status` and `report` showing open
  deferrals.
- A length bound on `reason` (ADR-0022 section 8 sets none for this field).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
