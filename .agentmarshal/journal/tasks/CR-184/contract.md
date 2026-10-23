+++
schema = 2
id = "CR-184"
title = "status shows the check, agreement, acknowledgement and ext records on lines of their own, who recorded them, and that a task has no agreement"
scope = [
  "src/agentmarshal/journal/status_view.py",
  "docs/sidecar.md",
  "tests/",
  "openspec/changes/status-schema-7-lines/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
  "openspec/specs/contract-governance/",
  "openspec/specs/leak-scan/",
  "openspec/specs/extension-records/",
]
acceptance = [
  "the change status-schema-7-lines has a proposal, a design.md and delta specs with ADDED requirements for the lines on the capabilities that own each record — review-evidence (check), contract-governance (agreement), leak-scan (acknowledgement), extension-records (ext); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`status <task>` renders, through the renderer registry, one line per `check` (name, result, short commit, failed step when present), `agreement` (short contract hash and who agreed), `acknowledgement` (short commit, the file as recorded, the signature or the marker's number, who acknowledged and the reason) and `ext` (kind, short commit, short payload hash) record; each line names the recorder, and a recorder that is not a declared actor is shown as not a declared actor (ADR-0022 section 3)",
  "an acknowledgement whose recorder is a declared author or committer of the acknowledged commit is marked self-acknowledged, derived on display the way self-acceptance is and never stored; where git cannot read the commit the line says the mark was not checked (ADR-0021 decision 5)",
  "a task with no agreement record prints one line saying no agreement is recorded; a task whose latest agreement's hash differs from the contract's current hash says the agreement is for an earlier text, naming both short hashes; neither line fails the command or changes the task's state (ADR-0018 decision 2: visibility, not a requirement)",
  "every value taken from a record is escaped on display as the other lines are; apart from the agreement line of the previous criterion, the lines of every other record type, the header, the drift line, the overdue-step and path output are unchanged — a test pins the detail view of a task carrying none of the four types byte for byte, agreement line included; the example `status` output in docs/sidecar.md shows the agreement line; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = [
  "openspec/specs/review-evidence/",
  "openspec/specs/contract-governance/",
  "openspec/specs/leak-scan/",
  "openspec/specs/extension-records/",
]
decisions = ["ADR-0017", "ADR-0018", "ADR-0021", "ADR-0022"]
+++

# status shows the schema-7 record types

## Context

CR-167, CR-170, CR-177 and CR-179 landed the `check`, `acknowledgement`,
`agreement` and `ext` records; `status` falls back to the generic id, type
and time line for each. The decisions pair every one of these records with
visibility: ADR-0021 decisions 4 and 5 — `status` shows who acknowledged
and marks a self-acknowledgement; ADR-0018 decision 2 — the absence of an
agreement is shown, instead of being indistinguishable from agreement never
asked for, and `status` shows who agreed; ADR-0022 section 3 — a recorder
that is not a declared actor is shown as such. The self-acceptance mark on
acceptance lines (`_is_self_accepted`) is the precedent for a mark derived
on display.

## Objective

A reader of `status` sees what each new record says and who said it.

## Acceptance Criteria

As in the header.

## Non-Goals

- The declared assignment (implementers, reviewers, independence) next to
  what ran (a later task in the same module).
- The gate's handling of acknowledged hits and of agreement
  (`require_agreement`), `report` (later tasks).
- Showing an ext record's payload: it is opaque to the core.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
