+++
schema = 2
id = "CR-219"
title = "The gate's operational lane: a candidate that changes only switches.toml and its own task's records passes without a review, and pre-gate stages do not run on it"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/stages.py",
  "tests/",
  "openspec/changes/gate-operational-lane/",
  "openspec/changes/archive/",
  "openspec/specs/gate-lanes/",
]
acceptance = [
  "the change gate-operational-lane has a proposal, a design.md and a delta spec on the capability gate-lanes with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "in the embedded placement, a candidate whose changes from the merge base are `.agentmarshal/switches.toml` and nothing else outside the task's own journal subtree takes the operational lane (ADR-0013 decision 17): the task's contract is read from the base when the task exists there, and otherwise is the one the candidate adds for this task — admitted because the lane itself bounds the diff, so the candidate's contract cannot widen it — and either way its scope must be exactly `[\".agentmarshal/switches.toml\"]`, or the candidate does not take the lane; the switches file at the candidate is parsed by CR-217's parser against the shared extensions declared at the base, and every entry added, changed or removed relative to the base names this task in its `task`; review, verdict, independence and agreement are not required and the transcript says so on one PASS line and NOT EXAMINED lines in the style of the journal-only lane; every other check of the candidate runs as it does today",
  "a candidate that also changes any other path — a manifest, any configuration, code — takes the lane it takes today and needs a review; a malformed switches file at the candidate, an entry naming another task, or an entry naming no shared extension declared at the base refuses the candidate naming the file and the entry; in a sidecar the operational lane is not offered and the transcript is unchanged",
  "`stage run --phase pre-gate` on a candidate that qualifies for the operational lane — decided by the same function the gate uses, imported, not copied — prints one line saying pre-gate stages do not run on an operational change and runs no stage, exit 0; every other phase and every other candidate behave as today",
  "the journal-only, findings and regular lanes print the transcript they print today byte for byte, which the existing pinned transcripts demonstrate unchanged; acceptance of an operational CR (`accept --operational`) is not read yet; every value from the file is escaped on display; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/gate-lanes/"]
decisions = ["ADR-0010", "ADR-0013", "ADR-0014", "ADR-0022"]
+++

# The gate's operational lane

## Context

ADR-0013 decision 17: an operational CR is a gate lane of its own, next to
the journal one — the diff touches only `.agentmarshal/switches.toml` and
its own task's records; no review is required (the one file excepted from
ADR-0010's rule that configuration is reviewed — a manifest still takes the
diff lane with review); extensions' `pre-gate` stages do not run on it,
otherwise a broken extension blocks its own switching off; the reason is
mandatory. CR-217 parses the file and reads it from the base; ADR-0014
places it. Opening such a CR with one command (`extension switch off`) and
the adopter's option to require operator acceptance instead of the fast
lane are later tasks.

## Objective

Switching a shared extension off is a change the gate admits without a
review, and only that change.

## Acceptance Criteria

As in the header.

## Non-Goals

- `agentmarshal extension switch off` (a later task).
- Requiring operator acceptance for an operational CR, and the gate reading
  `accept --operational` (a later task).
- The operational lane in a sidecar.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
