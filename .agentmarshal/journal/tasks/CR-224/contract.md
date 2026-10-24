+++
schema = 2
id = "CR-224"
title = "stage run honours an operator's acceptance of an extension's pause: a pre-gate-stop stage that failed or did not run, under an acceptance bound to the run's commit, is reported as accepted and does not pause the process"
scope = [
  "src/agentmarshal/stages.py",
  "tests/",
  "openspec/changes/stage-run-accepted-pause/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change stage-run-accepted-pause has a proposal, a design.md and a delta spec on the capability extension-stages (ADDED requirements, and MODIFIED where an existing requirement says a failed or not-run pre-gate-stop stage always pauses — the MODIFIED block carries the requirement's full text, heading byte for byte, every existing scenario); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`stage run --phase pre-gate` reads the task's acceptance records from the journal (through the existing record readers, not a second parser) and, for a `pre-gate-stop` stage that failed, did not finish or did not run, looks for an acceptance carrying `accepted_pause` naming that extension and `accepted_commit` equal to the commit the run resolved (ADR-0013 decision 5, ADR-0022 section 2); with one, the stage's result line keeps its outcome and adds `pause accepted by <party> (<reason>)`, the stage does not pause the process, and when no other stage pauses the command exits 0",
  "an acceptance bound to another commit, naming another extension, or of another form (over findings, operational) does not count; a switched-off stage is unchanged; a `pre-gate-warn` stage and a `post-gate` stage are unchanged; a stage that passed is unchanged and the acceptance is not mentioned",
  "the extension-event of an accepted pause carries the decision it carries today and a reason that names the acceptance record; every value from the record is escaped on display; a journal that cannot be read is named on one stderr line and every pause stands, never silently lifted",
  "the gate is unchanged (ADR-0013 decision 5: sorting out a pause does not touch the gate); `accept` is unchanged; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0007", "ADR-0013", "ADR-0022"]
+++

# stage run honours an accepted pause

## Context

ADR-0013 decision 5: an extension's stop is a pause of the process before
the gate; sorting it out — a fix in a new round, or operator acceptance —
does not touch the gate; the acceptance stands over the pause itself (the
first of two extensions of ADR-0007); the merge happens when the gate has
passed and no pause stands. CR-215 made `accept --task --commit --pause
<extension>` write that acceptance, bound by `accepted_commit`. CR-211's
`stage run` pauses (exit 3) on a failed, unfinished or not-run
`pre-gate-stop` stage and reads no acceptance yet.

## Objective

An operator's accepted pause lets the process continue for exactly the
commit and extension accepted, and the output says who accepted it.

## Acceptance Criteria

As in the header.

## Non-Goals

- `complete` running stages (a later task).
- The gate reading pause acceptances.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
