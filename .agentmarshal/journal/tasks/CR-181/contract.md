+++
schema = 2
id = "CR-181"
title = "Documentation: the implementer writes no local state, a contract may state a principle for a class of defects, the threat model lists every guarded field, a skipped required job is named"
scope = [
  "docs/harness-setup.md",
  "docs/quickstart.md",
  "docs/threat-model.md",
  "docs/github-enforcement.md",
  "docs/proposals/039-review-findings-do-not-feed-back-into-the-next-round.md",
]
acceptance = [
  "docs/harness-setup.md, under the rules that do not depend on the harness, adds that the implementer gets no write access to the clone's local state and to the user-level AgentMarshal directories — each location named as ADR-0014 and the code that resolves it name it — with the reason: they hold what records point to (review prose and diagnostics, the process log) and what decides trust and switches; a sandbox that leaves only the task worktree writable satisfies the rule",
  "docs/quickstart.md, in the section on the contract, describes principle criteria as proposal 039 asks and ADR-0016 accepts as documentation: a contract may state a class of defect and how the class is closed (an edge-case principle is the example), so a new instance of a covered class is reported as advisory unless the principle itself is violated; and a criterion over a large set of items names a mechanical check of the whole set shipped with the candidate — written as guidance to the contract's author, never as something the tool enforces",
  "docs/threat-model.md's enumeration of fields the forgeable-text rule refuses at write lists exactly the fields the record validators register for that rule today, checked against src/agentmarshal/journal/records.py; statements there made untrue by the record types and fields landed since it was written (agreement, review verification and evidence, ext) are corrected, and nothing is stated as enforced that only a later command will enforce",
  "docs/github-enforcement.md states, citing GitHub's documentation, that GitHub reports a job skipped by its condition as successful, that the shipped gate job runs only on pull-request events, and that a project adding another trigger a required check is evaluated on (a merge queue's `merge_group`, for example) must make the gate job run there, or the check passes unexamined",
  "proposal 039 carries a dated line saying where its contract principles are now written; no other document changes; every link added resolves; the suite and the full CI sequence pass",
]
documents = [
  "docs/harness-setup.md",
  "docs/quickstart.md",
  "docs/threat-model.md",
  "docs/github-enforcement.md",
  "docs/proposals/039-review-findings-do-not-feed-back-into-the-next-round.md",
]
decisions = ["ADR-0014", "ADR-0016", "ADR-0022"]
+++

# Documentation: four gaps before 0.5.0

## Context

Four places in the documentation trail what has been decided or landed:

- the harness rules say the agent must not write the journal, but say
  nothing of the local state ADR-0014 placed under the git common
  directory, nor of the user-level directories, which an implementer with
  the user's write rights could alter;
- proposal 039's disposition accepted principle criteria and the
  whole-set check "as documentation, to be written", and ADR-0016 refers to
  that contract guidance; it has not been written;
- the threat model's list of fields guarded by the forgeable-text rule
  predates the schema-7 record types and fields landed since (CR-173 to
  CR-179 — the implementer of CR-179 named the omission as a departure);
- the GitHub enforcement page does not say that a skipped required job
  counts as passing, which matters the moment a project adds a trigger the
  shipped gate job does not run on.

## Objective

A reader of these four documents learns what is true today, and nothing
more.

## Acceptance Criteria

As in the header.

## Non-Goals

- Release notes, UPGRADING and the quickstart's description of 0.5.0
  commands (the release documentation task).
- Any change to the review prompt or the reviewer protocol: the principle
  criteria are guidance for the contract's author.
- Rewording beyond the four gaps; cosmetic edits elsewhere.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
