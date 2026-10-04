+++
schema = 2
id = "CR-173"
title = "An acceptance of schema 7 can accept an extension pause or an operational CR; readers keep acceptance over findings to the acceptances that carry findings"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/status_view.py",
  "src/agentmarshal/journal/report.py",
  "tests/",
  "openspec/changes/pause-and-operational-acceptance/",
  "openspec/changes/archive/",
  "openspec/specs/operator-acceptance/",
]
acceptance = [
  "the change pause-and-operational-acceptance has a proposal, a design.md and a delta spec creating the capability operator-acceptance — its Purpose written in the delta — with ADDED requirements for the two new forms and for how the readers treat them; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "from schema 7 an `acceptance` record may carry, in place of `findings`, either `accepted_pause` — an object with exactly the key `extension`, whose value is a non-empty extension name that is one path component (the rule extension manifests apply to a name) and passes the forgeable-text rule — or `operational` with the value `true`; a record carrying more or fewer than exactly one of `findings`, `accepted_pause` and `operational` is refused with a message naming the three; both new forms bind by `accepted_commit` only and are refused with `accepted_finding`; `accepted_by` and `reason` are required as today",
  "an acceptance carrying `accepted_pause` or `operational` below schema 7 is refused at write and on read, and writing one stamps 7; an acceptance carrying `findings` is validated and stamped exactly as before; the new fields are declared through the record-type and field registrations the schema-7 record types use, not by a second mechanism",
  "no reader treats a pause or operational acceptance as an acceptance over findings, and none fails on an acceptance without `findings`: the gate, on both bindings, judges acceptance over findings by the latest acceptance of that commit or finding that carries `findings`; `status` prints a line for each new form naming `accepted_pause=<extension>` or `operational` where an acceptance over findings names its findings, with the same binding and self-acceptance marking; `report` derives `accepted-over-findings` only from an acceptance carrying `findings`; nothing else acts on the new forms",
  "every output for an acceptance carrying `findings` — the gate fixtures, the documented transcripts a test pins, the status and report lines — is unchanged byte for byte; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/operator-acceptance/"]
+++

# Acceptance of an extension pause and of an operational CR

## Context

ADR-0022 section 2 gives the `acceptance` record two new forms in schema 7,
from ADR-0013: `accepted_pause: {extension}`, bound by `accepted_commit` —
the acceptance of an extension pause, which raises no review finding
(ADR-0013 decision 5); and `operational: true` with `accepted_commit` — the
acceptance of an operational CR, which has no review at all (ADR-0013
decision 17). Both extend ADR-0007's acceptance; neither is a bypass of the
gate. The readers that exist today read `findings` from every acceptance
and take the latest acceptance of a commit as the one to judge — a pause
acceptance written after an acceptance over findings would shadow it, and
one without `findings` would fail them. The commands that write the new
forms, and the stages and the operational lane that act on them, are later
tasks.

## Objective

The journal can carry an accepted pause and an accepted operational CR, and
nothing that reads acceptances mistakes them for an acceptance over
findings.

## Acceptance Criteria

As in the header.

## Non-Goals

- The commands that write the new forms (`accept --pause`, `accept
  --operational`), extension stages, pauses, the operational lane, and any
  gate or `complete` behaviour that acts on a pause or an operational
  acceptance (later tasks).
- Any change to ADR-0007's rules for an acceptance over findings beyond
  keeping them to the acceptances that carry `findings`.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
