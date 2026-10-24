# extension-stages Specification (delta)

## Purpose

Release-audit finding AUD-extensions-1: the requirement promised a
containment the core does not enforce — a personal extension's process
runs with the developer's rights, so nothing beyond the stage isolation
stops it writing the journal's files. The restated requirement says
what the core enforces — no `ext` kind `record-ext` accepts, no
`footprint`, `documents` or `artifacts`, no effect on the gate or the
server-side process — and states the same-user caveat
docs/threat-model.md records.

## MODIFIED Requirements

### Requirement: a personal extension has no journal authority

A personal extension has no write path into the journal through the
core — `record-ext` SHALL accept only kinds a shared extension
declares, none a personal manifest's `[records]` declares — its
manifest SHALL carry no `footprint`, `documents` or `artifacts`, no
personal stage SHALL affect the gate or the server-side process, and
its `extension-event`s SHALL carry `scope` `personal`. Its process runs
with the developer's rights, not contained beyond the stage isolation
(docs/threat-model.md).

#### Scenario: record-ext refuses a kind only a personal manifest declares

`record-ext --kind mycheck/thing@1` — declared only by a personal
manifest — refuses the kind as undeclared and writes no record.

#### Scenario: a personal stage's extension-event carries the personal scope

A personal stage that runs writes an `extension-event` naming the
extension with `scope` `personal` and the decision and reason of the
outcome.

#### Scenario: a personal stage writes nothing to the journal

A run of personal stages appends no record and no `ext` record to the
journal; the process log gains only the stage's `extension-event`.
