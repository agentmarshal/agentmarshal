## MODIFIED Requirements

### Requirement: `status` shows the contract's declared assignment in a section of its own

`agentmarshal status <task>` SHALL print an assignment section — after
the task's scope and before the record lines — when the contract header
declares any of `implementers`, `reviewers` and `independence`, and
SHALL print no assignment section otherwise: a contract declaring none
of the three leaves the detail view byte for byte unchanged. The section
SHALL name the declared `implementers` and `reviewers`, each in its
declared order — the order is the fallback order — and the declared
`independence` rules, each field on a line of its own; the
`independence` line SHALL add `reviewer-not-writer` as always checked
by the gate when the header does not name it — the rule runs for every
candidate whether or not the header names it — so the line states the
rules in force, not only the rules declared. The section SHALL then
show what ran: the implementer-session lines in the order the records
stand, then the review lines in the order the records stand, as the
following requirements state — and an empty ran side SHALL say so the
way the scope section prints `(none)` for an empty scope: when the
contract declares `implementers` and no implementer session is
recorded, the section SHALL print `- implementer sessions: (none)`
where the implementer-session lines would stand, and when the contract
declares `reviewers` and no review is recorded, `- reviews: (none)`
where the review lines would stand. A ran side whose list the header
does not declare SHALL print no `(none)` line — `(not declared)`
already states that side has no assignment. A field the header does not
declare SHALL be shown as not declared rather than omitted (ADR-0018
decision 3).

#### Scenario: a contract declaring all three prints the section
- **WHEN** the contract header declares `implementers`, `reviewers` and
  `independence`
- **THEN** `status <task>` prints an assignment section naming the three
  lists — implementers and reviewers in their declared order — after the
  scope and before the record lines

#### Scenario: an undeclared field is shown as not declared
- **WHEN** the contract header declares `implementers` but neither
  `reviewers` nor `independence`
- **THEN** the section names the declared implementers, shows
  `reviewers` as not declared, and the `independence` line shows the
  field as not declared and names `reviewer-not-writer` as always
  checked by the gate

#### Scenario: reviewer-not-writer the header does not name is named as always checked
- **WHEN** the contract header declares `independence` without
  `reviewer-not-writer`
- **THEN** the `independence` line names the declared rules and adds
  `reviewer-not-writer (always checked by the gate)`

#### Scenario: sessions group before reviews whatever the record order
- **WHEN** the task's records stand with a review before an implementer
  session
- **THEN** the section prints the implementer-session lines first and
  the review lines after, each in the order the records stand

#### Scenario: a contract declaring none prints today's view byte for byte
- **WHEN** the contract header declares none of the three fields
- **THEN** `status <task>` prints no assignment section, and the detail
  view is byte for byte what it was

#### Scenario: a declared implementers list with no session recorded says none
- **WHEN** the contract header declares `implementers` and the task
  carries no implementer session
- **THEN** the section prints `- implementer sessions: (none)` where the
  implementer-session lines would stand

#### Scenario: a declared reviewers list with no review recorded says none
- **WHEN** the contract header declares `implementers` and `reviewers`,
  an implementer session is recorded and no review is recorded
- **THEN** the section prints `- reviews: (none)` where the review lines
  would stand, after the implementer-session lines

#### Scenario: a side with no declared list prints no (none) line
- **WHEN** the contract header declares `independence` alone and the
  task carries neither an implementer session nor a review
- **THEN** the section ends at the declaration lines — neither ran side
  prints a `(none)` line, `(not declared)` already stating the absence
