+++
schema = 2
id = "CR-096"
title = "The material that carries a contract carries its amendment history, and a review names the contract it judged"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/brief.py",
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/submit_review.py",
  "tests/test_review_launcher.py",
  "tests/test_brief.py",
  "tests/test_journal.py",
  "tests/test_attestation.py",
  "docs/quickstart.md",
  "openspec/changes/render-amendment-history/",
  "openspec/changes/archive/",
  "openspec/specs/contract-history/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "every scenario in openspec/changes/render-amendment-history/specs/ is demonstrated by a test whose docstring names it, and the implementation follows design.md's decisions or records in design.md why it departed",
  "a task whose journal holds no amendment record produces the prompt and the brief it produced before this change: the pinned 0.3.0 prompt test and the gate transcript tests pass with their expectations unmodified",
  "the rendering reads amendment records from the journal the command works in, so an amendment recorded after the reviewed commit reaches the prompt for that commit; the contract itself is read from the side each command reads it from today",
  "reviewed_contract is allowed by a new record schema, a writer stamps it only on a record that carries the field, a record carrying it under an earlier schema is refused with a message naming the field, and this journal's existing records validate unchanged",
  "no line is added to the gate in any placement or lane, and tasks.md's checkboxes are ticked for the work that landed",
]
decisions = ["ADR-0004", "ADR-0011"]
documents = ["openspec/changes/render-amendment-history/", "openspec/specs/review-evidence/"]
+++

# CR-096: the amendment history reaches the reader, and the review names its contract

## Context

ADR-0011 landed as a decision with no mechanism. This task is the mechanism, and
it is the fourth product task run with an OpenSpec delta spec under the research
protocol. The proposal that prompted the decision came from an adopter running
the published release; their measurement is quoted in the digest the decision
cites.

## Objective

The reviewer and the implementer are told that the contract was amended, when
and why. A review record says which contract text it judged.

## Acceptance Criteria

As in the header. The spec's scenarios are the behaviour; design.md's decisions
are the shape; tasks.md is the checklist the implementer ticks.

## Threat model and boundaries

The party that amends a contract is usually the party that orchestrates the
implementer and requests the review. This task does not add a refusal anywhere;
it removes the asymmetry where the one independent reader was the one reader not
told. The rendering is built from records and never by parsing the contract
document, which ADR-0004 D3 forbids the gate to do and which an earlier draft of
ADR-0011 got wrong.

## Amended 2026-09-17

`tests/test_attestation.py` joins the scope. It pinned schema 5 as an unknown
schema; adding 5 to the ladder makes that test wrong, and the test names the
next unknown number instead. The schema ladder in this model is shared across
record types — `schema >= 2` opens provenance for every type and schema 4 is
bound to fields rather than to a type — so a record of any type may declare 5
without carrying the new field, exactly as it may declare 4 today.

## Non-Goals

- Any gate check, line or refusal, in any placement or on any lane.
- Writing into `contract.md`: `amend` is untouched.
- The findings lane, and whether a sidecar gate should speak on a
  `reviewed_contract` mismatch: ADR-0011 leaves both open.
- Rendering *what* changed in an amendment; the record carries a reason, not a
  diff.
