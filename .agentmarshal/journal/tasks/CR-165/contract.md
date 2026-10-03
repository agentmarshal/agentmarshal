+++
schema = 2
id = "CR-165"
title = "doctor prints where the journal, the process log and the local state are, reports overdue steps, and names the git version local state needs"
scope = [
  "src/agentmarshal/doctor.py",
  "tests/",
  "openspec/changes/doctor-steps-paths-git/",
  "openspec/changes/archive/",
  "openspec/specs/process-log/",
  "openspec/specs/local-state/",
]
acceptance = [
  "the change doctor-steps-paths-git has a proposal, a design.md and a delta spec adding to process-log what doctor reports about steps and paths and to local-state the git version it needs (MODIFIED with exact headers where an existing requirement changes); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal doctor` prints the actual paths of the journal, the process log and the local state in use (ADR-0014 decision 13), each on its own line and escaped like other displayed text; in a sidecar the journal and the local state are the journal repository's",
  "doctor lists every overdue step across the project's tasks, using the same open/overdue computation `status` uses (steps.py), as a report: an overdue step never makes doctor exit non-zero, and an unreadable process log is named, not a failure",
  "doctor's git check names the minimum git version local state needs (2.31, for `rev-parse --path-format=absolute`) and fails, with the remedy (upgrade git) in the message, when the installed git is older; the version is parsed from `git --version` output without depending on the platform suffix; a test patches the reported version both ways",
  "every existing doctor check reports as before, and the full CI sequence passes",
]
documents = ["openspec/specs/process-log/", "openspec/specs/local-state/"]
+++

# CR-165: doctor — steps, paths and the git version

## Context

ADR-0014 decision 9 (as amended) and decision 13: `status` and `doctor` show
a step past its deadline and print the actual paths. CR-162 did it for
`status`. CR-148's review noted that local state resolves through `git
rev-parse --path-format=absolute`, which git older than 2.31 does not know —
`doctor` is where a missing precondition is named.

## Objective

`doctor` tells an operator where everything lives, which steps ran past
their deadline, and whether their git can resolve local state.

## Acceptance Criteria

As in the header.

## Non-Goals

- Extension checks in doctor (a later task).
- Stopping any process.
