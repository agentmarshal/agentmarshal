+++
schema = 2
id = "CR-178"
title = "A review record of schema 7 may say what the reviewer executed, read and could not run, and carry evidence for its findings"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "tests/",
  "openspec/changes/review-verification-and-evidence/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change review-verification-and-evidence has a proposal, a design.md and a delta spec adding to review-evidence the two fields (ADDED requirements; MODIFIED with exact headers only where one becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "from schema 7 a `review` record may carry `verification` — an object with one or more of the keys `executed`, `read` and `not_run` and no other key: `executed` a non-empty array of objects with exactly `what` and `result`, `read` a non-empty array of strings, `not_run` a non-empty array of objects with exactly `what` and `why`; every string in it non-empty and passing the forgeable-text rule — each refusal naming the key and the position at fault",
  "from schema 7 a `review` record may carry `evidence` — a non-empty object whose every key is a finding id the same record names in `findings` or `advisory_findings` and whose every value is a non-empty string passing the forgeable-text rule (ADR-0017 decision 5: a link, a file:line, or a command with the essential part of its output)",
  "a review carrying either field below schema 7 is refused at write and on read, and writing one stamps 7; a review carrying neither is validated and stamped exactly as before; the fields are declared through the registrations the schema-7 review fields of CR-174 use, not by a second mechanism; no other record type changes and nothing reads or writes the fields yet",
  "the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/"]
+++

# What a verdict says was executed, and evidence for findings

## Context

ADR-0017 decision 4: the verdict says what was executed and what was read —
an optional section of the reviewer protocol: what the reviewer ran and
with what result, what it checked by reading only, and what it could not
run and why. Decision 5: a finding carries an optional evidence reference —
a link, a `file:line`, or the command that checked the claim with the
essential part of its output. ADR-0022 section 2 names the fields
`verification` and `evidence` on the `review` record in schema 7. The
resolution-only review mode in the same section is not part of this task
(its proposal is under review). The protocol lines that ask the reviewer
for these sections, and every reader, are later tasks.

## Objective

The journal can carry what a review executed and read, and the evidence
behind its findings.

## Acceptance Criteria

As in the header.

## Non-Goals

- The review protocol asking for the sections, the launcher writing them,
  the "unconfirmed" advisory line, and any reader (later tasks).
- `mode: resolution` and `carried_approval` (blocked pending the review of
  the queue model).
- A length bound on the fields (ADR-0022 section 8 sets none for them).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
