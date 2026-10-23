## ADDED Requirements

### Requirement: `status` shows the contract's declared assignment in a section of its own

`agentmarshal status <task>` SHALL print an assignment section — after
the task's scope and before the record lines — when the contract header
declares any of `implementers`, `reviewers` and `independence`, and
SHALL print no assignment section otherwise: a contract declaring none
of the three leaves the detail view byte for byte unchanged. The section
SHALL name the declared `implementers` and `reviewers`, each in its
declared order — the order is the fallback order — and the declared
`independence` rules, each field on a line of its own, and SHALL then
show what ran: the implementer-session lines in the order the records
stand, then the review lines in the order the records stand, as the
following requirements state. A field the header does not declare SHALL
be shown as not declared rather than omitted (ADR-0018 decision 3).

#### Scenario: a contract declaring all three prints the section
- **WHEN** the contract header declares `implementers`, `reviewers` and
  `independence`
- **THEN** `status <task>` prints an assignment section naming the three
  lists — implementers and reviewers in their declared order — after the
  scope and before the record lines

#### Scenario: an undeclared field is shown as not declared
- **WHEN** the contract header declares `implementers` but neither
  `reviewers` nor `independence`
- **THEN** the section names the declared implementers and shows the two
  undeclared fields as not declared

#### Scenario: a contract declaring none prints today's view byte for byte
- **WHEN** the contract header declares none of the three fields
- **THEN** `status <task>` prints no assignment section, and the detail
  view is byte for byte what it was

### Requirement: `status` shows which implementer sessions ran

For each implementer session — a session record of the task whose `role`
is `implementer` — the assignment section SHALL print one line naming
the record's id and showing the session's `actor`, the vendor read from
`usage.provider`, the session's `model`, and `fallback_reason` when the
record carries one. An absent value SHALL be shown as absent, never
derived from another field: the vendor comes from `usage.provider`
alone, never guessed from the actor or the model. A session whose
`actor` is not in the declared `implementers` SHALL be marked as not
declared for the role — shown, not refused (ADR-0018 decision 3). The
mark SHALL appear only when the contract declares `implementers`; a
session carrying no actor shows the absent value and no mark. A session
of another `role` prints no implementer-session line.

#### Scenario: an implementer session's line shows what ran
- **WHEN** a task carries an implementer session — a session record
  whose `role` is `implementer`
- **THEN** its assignment-section line names the record's id and shows
  the session's `actor`, the vendor from `usage.provider`, its `model`
  and its `fallback_reason`

#### Scenario: the vendor is read from usage.provider alone
- **WHEN** an implementer session carries no `usage` and its `actor`
  reads like `openai/gpt-5`
- **THEN** the line shows the vendor as absent, never guessed from the
  actor string

#### Scenario: an absent value is shown as absent
- **WHEN** an implementer session carries no `model` or no `actor`
- **THEN** the line shows the absent value as absent

#### Scenario: fallback_reason prints only when the record carries it
- **WHEN** one implementer session carries `fallback_reason` and another
  does not
- **THEN** the first session's line shows it and the second's shows no
  `fallback_reason`

#### Scenario: an actor not in the declared list is marked
- **WHEN** the contract declares `implementers` and an implementer
  session's `actor` is not in the list
- **THEN** the line shows the actor and marks it as not declared for the
  role — shown, not refused

#### Scenario: an actor in the declared list carries no mark
- **WHEN** the contract declares `implementers` and an implementer
  session's `actor` is in the list
- **THEN** the line carries no not-declared mark

#### Scenario: the mark appears only when implementers is declared
- **WHEN** the contract declares no `implementers` and an implementer
  session runs
- **THEN** the line shows the session's actor with no not-declared mark

#### Scenario: a session of another role prints no implementer-session line
- **WHEN** the task carries a session record whose `role` is not
  `implementer`
- **THEN** the section prints no implementer-session line for it

### Requirement: `status` shows which reviews ran

For each review record of the task the assignment section SHALL print
one line naming the record's id and showing its reviewer's `actor`,
`vendor` and `model`, an absent value shown as absent. A review whose
`reviewer.actor` is not in the declared `reviewers` SHALL be marked as
not declared for the role — shown, not refused (ADR-0018 decision 3).
The mark SHALL appear only when the contract declares `reviewers`; a
review carrying no `reviewer.actor` shows the absent value and no mark.

#### Scenario: a review's line shows what ran
- **WHEN** a task carries a review record
- **THEN** its assignment-section line names the record's id and shows
  the reviewer's `actor`, `vendor` and `model`

#### Scenario: an absent reviewer value is shown as absent
- **WHEN** a review's `reviewer` object carries no `actor`
- **THEN** the line shows the absent value and no not-declared mark

#### Scenario: a reviewer actor not in the declared list is marked
- **WHEN** the contract declares `reviewers` and a review's
  `reviewer.actor` is not in the list
- **THEN** the line shows the actor and marks it as not declared for the
  role

#### Scenario: the mark appears only when reviewers is declared
- **WHEN** the contract declares no `reviewers` and a review runs
- **THEN** the line shows the reviewer's `actor` with no not-declared
  mark

### Requirement: the assignment section's values are escaped on display

Every value the assignment section takes from a contract or a record
SHALL be escaped on display as the record lines' values are: each
refused character prints as its escape and the line stays one line.
Nothing else `status` prints SHALL change — the record lines, the
agreement line, the drift line, the overdue-step and path lines — and no
other command changes.

#### Scenario: a value that could forge a line prints escaped
- **WHEN** a value the section prints — a declared list entry, a
  session's or a review's field — carries a character that could add a
  line to rendered output or reorder it
- **THEN** each refused character prints as its escape and the line
  stays on its own line

## MODIFIED Requirements

### Requirement: Contract header schema 3 declares the assignment and the independence rules in force

A header with `schema = 3` MAY carry `implementers` and `reviewers`, each an
ordered list of non-empty actor ids — the order is the fallback order — and
`independence`, a list drawn from exactly `reviewer-not-writer`,
`distinct-actor`, `distinct-vendor` and `distinct-model`. Each of the three
fields is optional; absent, it SHALL parse as empty. The parsed header SHALL
expose the three fields, and a schema-3 header MAY carry every field a
schema-2 header carries. The gate SHALL read `independence` and check the
declared rules at the merge boundary as this capability's gate requirements
state; `status` SHALL read `implementers` and `reviewers` and show the
declared assignment next to what ran, as this capability's `status`
requirements state.

#### Scenario: the assignment lists keep their declared order
- **WHEN** a schema-3 header lists `implementers` as `['devin', 'codex',
  'devin-ci']` and `independence` as `['reviewer-not-writer',
  'distinct-actor', 'distinct-vendor', 'distinct-model']`
- **THEN** the parsed header's `implementers` is `('devin', 'codex',
  'devin-ci')` and its `independence` is `('reviewer-not-writer',
  'distinct-actor', 'distinct-vendor', 'distinct-model')`

#### Scenario: each field is optional
- **WHEN** a schema-3 header carries none of `implementers`, `reviewers` and
  `independence`
- **THEN** it parses, and the parsed header's three fields are empty

#### Scenario: a schema-3 header may carry the schema-2 fields
- **WHEN** a schema-3 header carries `decisions`, `documents` or
  `extensions`
- **THEN** they parse as they do under schema 2
