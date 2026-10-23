+++
schema = 2
id = "CR-189"
title = "brief carries the task's last failing check: its name, commit, failed step, excerpt and run link, and whether a later run passed"
scope = [
  "src/agentmarshal/journal/brief.py",
  "tests/",
  "openspec/changes/brief-last-failing-check/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change brief-last-failing-check has a proposal, a design.md and a delta spec on the capability review-evidence with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal brief --task <id>` adds one section naming the task's most recent `check` record whose result is `failed` or `error`: the check's name, its result, the short commit, the failed step and the run link when the record carries them, and the excerpt when it carries one — every value escaped on display as the rest of the brief is",
  "when a later `check` record of the same name passed on a later commit, the section says so, naming that commit, so a fix round is not sent after a failure already fixed; when the task has no failing check, the brief carries no such section and is otherwise unchanged",
  "the section states that a check record is the observer's declaration, not proof, in one sentence (ADR-0017 decision 2); the brief of a task without check records is byte for byte what it is today, which a test pins",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/"]
decisions = ["ADR-0017", "ADR-0022"]
+++

# brief carries the last failing check

## Context

ADR-0017 decision 3: `brief` carries the last failing `check` of the task,
so the implementer of a fix round starts from what the pipeline found,
not only from the reviewer's opinion. Decision 2: the gate decides
nothing from a check record — it is the observer's declaration. CR-167
landed the record and CR-183 the command that writes it, with a masked
excerpt of at most 4 KiB.

## Objective

The implementer's briefing says what the pipeline last refused and why.

## Acceptance Criteria

As in the header.

## Non-Goals

- `report` counting rejected candidates (a later task).
- Reading the full output from the process log into the brief: the excerpt
  on the record is what the brief carries.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
