+++
schema = 2
id = "CR-199"
title = "report sums cost per currency, counts the candidates a pipeline check refused, and with --findings shows finding classes and open deferrals across tasks"
scope = [
  "src/agentmarshal/journal/report.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/report-cost-checks-findings/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
  "openspec/specs/finding-lifecycle/",
]
acceptance = [
  "the change report-cost-checks-findings has a proposal, a design.md and delta specs on the capabilities session-activity (cost, checks) and finding-lifecycle (findings view) with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`report` (per task and in aggregate) sums the sessions' `cost` per currency — one sum per currency, never converted or blended, `reported` and `estimated` summed separately — and says how many sessions carry no cost; a task with no cost shows none rather than zero (ADR-0019 decision 4)",
  "`report` counts per task the distinct commits a `check` record marked `failed` or `error`, next to the review rounds, and in aggregate (ADR-0017 decision 3); a check record is the observer's declaration, and the report says so once",
  "`report --findings` lists the finding classes recorded on reviews across tasks with a count and up to three example finding ids each (ADR-0016 decision 3), and the deferred advisory dispositions of completed tasks still open — those whose follow-up names no task, or a task the journal does not hold as completed — with task, finding id, reason and follow-up (ADR-0016 decision 1)",
  "what `report` prints today stays first and unchanged, which a test pins; every value from a record is escaped on display; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/", "openspec/specs/finding-lifecycle/"]
decisions = ["ADR-0016", "ADR-0017", "ADR-0019", "ADR-0022"]
+++

# report: money, refused checks, findings

## Context

ADR-0019 decision 4: `report` sums cost per currency and converts nothing.
ADR-0017 decision 3: `report` counts the candidates the pipeline rejected,
next to rounds and cost. ADR-0016 decision 3: `report --findings` shows the
classes across tasks, with counts and examples; decision 1: `status` and
`report` show the deferrals still open. The fields landed with CR-174
(classes), CR-175/CR-192 (dispositions), CR-167/CR-183 (check records),
CR-176/CR-188 (cost); CR-196 added lead time to `report`.

## Objective

The aggregate view says what the work cost in each currency, how often the
pipeline refused, which kinds of defect recur, and what was left for later.

## Acceptance Criteria

As in the header.

## Non-Goals

- Currency conversion, price lists, or estimating a cost from tokens.
- Review-by dates on deferrals (pending an operator decision).
- Counting resolution-mode reviews (the mode is not implemented).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
