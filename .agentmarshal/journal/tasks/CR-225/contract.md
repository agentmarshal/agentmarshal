+++
schema = 2
id = "CR-225"
title = "complete runs the extensions' stages: pre-gate stages before it records completion — a stop pauses while the candidate is unmerged and warns once it is merged — and post-gate stages after"
scope = [
  "src/agentmarshal/stages.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/complete-runs-stages/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
]
acceptance = [
  "the change complete-runs-stages has a proposal, a design.md and a delta spec on the capability extension-stages with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "the stage runner `stage run` uses becomes one function both commands call (stage run's own output and exit statuses unchanged, which its existing tests demonstrate); `complete --task --commit --base` calls it for `pre-gate` with the same commit and base before its gate check and before anything is written (ADR-0013 decision 2)",
  "`complete` gains an optional `--target <ref>` naming the branch the candidate merges into — distinct from `--base`, which stays the merge base the gate diffs against (a wrapper passes the pre-merge merge base even after the merge); while the candidate commit is not an ancestor of `--target`, or when `--target` is not given, a `pre-gate-stop` stage that pauses (failed, unfinished or not run, and not covered by an accepted pause as CR-224 reads it) refuses the completion: the stage lines and one line saying the completion is paused are printed, nothing is written, and the exit status is the one `stage run` uses for a pause; once the candidate is an ancestor of `--target` (already merged), the same stage is reported as a warning and the completion proceeds and writes `completed`",
  "after the `completed` record is written, `complete` calls the runner for `post-gate`; a post-gate result never changes complete's exit status or its record (a notification, ADR-0013 decision 4); a project with no shared extension that declares a stage prints exactly what `complete` prints today, which the existing complete tests demonstrate unchanged; `complete --findings` (no candidate) runs no stage",
  "the gate is unchanged; switched-off and accepted-pause outcomes behave as in `stage run`; every value is escaped on display; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-stages/"]
decisions = ["ADR-0013", "ADR-0016", "ADR-0022"]
+++

# complete runs the stages

## Context

ADR-0013 decision 2: two stages — `pre-gate` (in CI and at the merge step,
before the gate) and `post-gate` (after `complete`). Inside `complete` —
which may run before or after the implementation merges — a `pre-gate-stop`
pause applies while the candidate is not yet merged into the target
branch, and is reported as a warning once it is. Decision 4: `post-gate` is
a notification. CR-211 built `stage run`; CR-217 switches; CR-221/CR-223
isolation; CR-224 accepted pauses.

## Objective

Completing a task runs the same checks `stage run` runs, at the moments the
decision names, without changing the gate or a project that has no
extensions.

## Acceptance Criteria

As in the header.

## Non-Goals

- Running stages from the gate or from `review`.
- New stages beyond `pre-gate` and `post-gate`.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
