+++
schema = 2
id = "CR-204"
title = "Release 0.5.0"
scope = [
  "CHANGELOG.md",
  "UPGRADING.md",
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
  "README.md",
  "docs/quickstart.md",
]
acceptance = [
  "CHANGELOG.md has a 0.5.0 section dated the day of the release, grouped by subject, in which every entry names the tasks it comes from and describes only merged behaviour; every task completed since v0.4.1 (CR-116 to CR-203 in this journal) is either named in an entry or listed in one closing line of documentation-only and process tasks; the section opens with the record-schema transition and a pointer to UPGRADING.md",
  "the 0.5.0 section has a paragraph stating what was decided but is not in this release — executing extensions (stages, isolation, trust, switches, pause, the operational lane; ADR-0013), `next` and the plan file (ADR-0023, ADR-0022 section 7), the watchdog and monitor, the merge slot and the resolution-mode review (proposals 042, 043), the unfinished-candidate override and review-by dates (to arrive under a later record schema), raw provider exports — each with the decision that holds it, and nothing presented as shipped that is not",
  "UPGRADING.md has a 0.4.1 -> 0.5.0 section stating ADR-0022 section 1's upgrade rule — every clone and every CI job moves to 0.5.0 before the first 0.5.0 record is written, because a task opened on 0.5.0 carries a schema-7 record from its first write — and what a 0.4.x installation does with a schema-7 record, a schema-3 contract header, a schema-2 or directory-form manifest and the new project.json keys, as that section states; it names the new commands and the new project.json keys",
  "the package version is 0.5.0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, the smoke test asserts it, and `agentmarshal --version` prints it; docs/quickstart.md's sentence that the review prompt states all of the class handling (CR-185's deferred advisory) says only what the prompt states; no statement in README.md or docs/quickstart.md presents an unreleased feature as available",
  "no statement about 0.4.x as history changes; the gate's fixtures and every documented transcript a test pins are unchanged; the full CI sequence passes",
]
documents = ["CHANGELOG.md", "UPGRADING.md"]
decisions = ["ADR-0013", "ADR-0016", "ADR-0017", "ADR-0018", "ADR-0019", "ADR-0021", "ADR-0022", "ADR-0023"]
+++

# Release 0.5.0

## Context

0.5.0 carries the record model of ADR-0022: one transition to record schema
7, contract header schema 3 and manifest schema 2, the new record types
(`check`, `agreement`, `acknowledgement`, `ext`) and fields, and the
commands and checks that write and read them, landed as CR-145 to CR-203.
The operator decided on 2026-10-23 what 0.5.0 leaves out: executing
extensions moves to 0.6; `next`, the plan file, the driver, the watchdog,
the merge slot and the resolution-mode review stay decided but unshipped
while the queue model is under review; the unfinished-candidate override
and review-by dates arrive after the release under a later record schema.

The release workflow publishes on a `v*` tag whose name equals the
pyproject version and refuses a development version (CR-112). Tagging and
publishing follow this task's merge; the default branch returns to a
development version in a task of its own.

## Objective

0.5.0 can be published with notes that say exactly what it does, what it
does not, and how to upgrade.

## Acceptance Criteria

As in the header.

## Non-Goals

- Tagging, publishing, and the post-release development version (after
  this task).
- Rewriting the per-feature documentation landed with each task.
- The adopter handoff (prepared separately).
