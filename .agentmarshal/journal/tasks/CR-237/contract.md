+++
schema = 2
id = "CR-237"
title = "The gate and report mark a self-acceptance, and report classifies a completion by the review and acceptance that apply to the completed commit"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/report.py",
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "openspec/changes/self-acceptance-on-every-surface/",
  "openspec/changes/archive/",
  "openspec/specs/operator-acceptance/",
]
acceptance = [
  "where an acceptance's accepting party matches a declared writer of the candidate (the identities the gate's independence check already reads), the gate's acceptance line says so in the terms status uses (self-accepted, with the declared-identity qualification), judged over every commit of the candidate range, and `report`'s line for the task carries the same mark, judged — like status — over the accepted commit, because the journal records no candidate base; the requirement states both conditions and that report and status therefore do not mark a self-acceptance by a writer of an earlier commit of the range only (that residue waits for a record field carrying the base, with the next record schema); ADR-0007 decision 4 (release-audit finding AUD-gate-journal-5)",
  "`report`'s decision for a completed task is derived from the review and acceptance that apply to the completed commit: a task whose completed commit has an approving latest review is reported as closed on approval even if an earlier commit was accepted over findings; a task completed over findings on the completed commit is reported as accepted-over-findings as today (ADR-0007 decision 5; AUD-gate-journal-4)",
  "the change self-acceptance-on-every-surface carries a delta on operator-acceptance (MODIFIED with the full current text, heading byte for byte and every scenario, for every requirement whose byte-for-byte output clause the new mark touches; ADDED for the new behaviour) whose scenarios are each demonstrated by a test whose docstring names it; archived with the archive command (OpenSpec 1.15.0)",
  "a journal with no self-acceptance and no earlier acceptance prints exactly what it prints today, which the existing gate, report and status tests and transcript fixtures demonstrate unchanged; every value shown is escaped as today; the suite and the full CI sequence pass",
]
documents = ["openspec/specs/operator-acceptance/"]
decisions = ["ADR-0007"]
+++

# Self-acceptance on every surface

## Context

Release audit 0.6.0, area gate-journal, findings AUD-gate-journal-5 and
-4 (confirmed by reproduction): status marks a self-acceptance, but the
gate's acceptance line and report do not, while ADR-0007 decision 4 and
docs/threat-model.md promise the mark on every surface. Report marks a
task accepted-over-findings whenever any acceptance carrying findings
exists, even when the completed commit was approved — ADR-0007
decision 5 asks report to distinguish the two.

## Objective

Every surface shows a self-acceptance as such, and report says how the
completed commit actually closed.

## Acceptance Criteria

As in the header.

## Non-Goals

- Changing who may accept, or the gate's admission rules.
- status (already marks self-acceptance).
