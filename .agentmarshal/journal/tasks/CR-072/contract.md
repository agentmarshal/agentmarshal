+++
schema = 1
id = "CR-072"
title = "A changelog for everything since 0.1.0"
scope = ["CHANGELOG.md", "UPGRADING.md"]
acceptance = [
  "CHANGELOG.md exists and records 0.2.0 and the released 0.1.0",
  "the 0.2.0 entry is grouped by what a reader can do differently, not by commit or task order",
  "it states the journal-format break: a journal written by 0.2.0 is refused by 0.1.0, and 0.2.0 reads everything 0.1.0 wrote",
  "it names the commands that are new and the one that was renamed before release",
  "every claim about what the software does is checkable against the repository; a release date is cited to the index that holds it, and nothing roadmap is described as shipped",
  "UPGRADING.md exists and gives the procedure per installation method, and the changelog links to it",
]
+++

# CR-072: A changelog for everything since 0.1.0

## Context

0.1.0 is on PyPI. **Thirty-three tasks** have completed since, and the
repository has no changelog at all — the record of what changed lives in commit
messages and journal records, which is the right place for evidence and the
wrong place for a reader deciding whether to upgrade.

Some of what landed is user-visible in ways an adopter must know about before
upgrading rather than after: the journal format moved, two new commands exist,
one command was renamed, and the gate gained a second path to passing its review
check.

## Objective

Write the changelog that should have accompanied the work, so the release can
be read rather than reconstructed — and the upgrade guide it has to point at.

## Acceptance Criteria

- `CHANGELOG.md` exists at the repository root, recording **0.2.0** and the
  already-released **0.1.0**.
- The 0.2.0 entry is grouped by what a reader can now do differently — not by
  commit order, and not as a list of task ids.
- It states the format break plainly: a journal written by 0.2.0 is refused by
  0.1.0, and 0.2.0 reads everything 0.1.0 wrote. It points at the upgrade
  guidance rather than repeating it.
- It names what is new (`accept`, `amend`, `brief`, `reopen`, `prune`) and that
  `prune-branches` was renamed to `prune` before ever being released.
- **Every claim about what the software does is checkable against this
  repository**, and nothing on the roadmap is described as shipped. Where a
  capability is partial, it says so.

  A release date is the exception, and is not one by oversight: when a version
  shipped is a fact about the index that holds it, not about this repository —
  the git tag carries a local timestamp that can read a day either side. Dates
  are therefore cited to the index, which anyone can check.

## Threat model and boundaries

A document. Nothing executes.

The failure worth guarding against is the one this project has a memory of:
**overclaiming**. A changelog is where a project is most tempted to describe
intent as achievement — signing, attestation completeness, enforcement that is
advisory. Each entry must survive being checked against the code by a reader who
is unimpressed.

Not in this task's reach: whether the version number is right, or whether the
release is published. Those follow.

## Non-Goals

- **Bumping the version, tagging, or publishing.** Separate tasks; this one only
  writes the record.
- Instructions for anything but upgrading from 0.1.0 to 0.2.0. The guide covers
  this transition, not a general migration manual.
- Rewriting history or back-filling entries for versions before 0.1.0.
- Describing internal refactors an adopter cannot observe.
