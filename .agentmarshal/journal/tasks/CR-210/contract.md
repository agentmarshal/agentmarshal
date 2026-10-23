+++
schema = 2
id = "CR-210"
title = "The gate warns when a candidate adds another task's opened or amendment records, and status --base lists a task's records the base does not hold"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/status_view.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/other-task-records/",
  "openspec/changes/archive/",
  "openspec/specs/gate-lanes/",
  "openspec/specs/record-lifecycle/",
]
acceptance = [
  "the change other-task-records has a proposal, a design.md and delta specs on gate-lanes (the warning) and record-lifecycle (the listing) with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "when a candidate adds an `opened` or `amendment` record under the journal directory of a task other than the task the gate is judging, the gate prints one WARN line naming each such task and the record kinds — the records stay valid evidence and nothing is refused (proposal 035's disposition); a candidate adding no such record produces today's transcript byte for byte, which the pinned default transcript and the fixtures demonstrate",
  "`agentmarshal status <task> --base <ref>` prints, after today's detail view, the task's records present in the journal's working tree but absent from `<ref>` — one line each, with id and type — or one line saying there are none; without `--base` the command prints exactly what it prints today; an unknown ref refuses naming it",
  "every value from a record or a path is escaped on display as the other lines are; the sidecar placement compares against the journal repository's ref, and says so in design.md",
  "no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/gate-lanes/", "openspec/specs/record-lifecycle/"]
decisions = ["ADR-0004", "ADR-0012"]
+++

# Records of another task, and records not yet published

## Context

Proposal 035: more than a quarter of one adopter's journal transactions
carried other tasks' records. Its disposition, together with proposal
019's, ships a transaction script that stages only its own task (CR-207)
and, with it, two read-side signals: the gate warns when a transaction adds
`opened` or `amendment` records of a task it does not name — the reporter's
lesser option; the records stay valid evidence, what was wrong is which
transaction carried them — and `status` lists the records present in the
working tree but not on the base branch. The base is named explicitly
rather than guessed, as the gate's own `--base` is.

## Objective

A record that travels in the wrong transaction, and a record not yet
published, are visible.

## Acceptance Criteria

As in the header.

## Non-Goals

- Refusing a candidate over another task's records.
- Staging or publishing anything (the transaction script does that).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
