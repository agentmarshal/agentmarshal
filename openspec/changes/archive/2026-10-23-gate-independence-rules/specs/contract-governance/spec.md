## Purpose

The gate's reading of the independence rules a schema-3 contract header
declares — how each rule is judged at the merge boundary, and what the
transcript says where a rule cannot be judged.

## ADDED Requirements

### Requirement: The gate checks the independence rules the contract declares

When the contract the gate reads — the merge-base tree's in the embedded
placement, the sidecar working tree's in the sidecar placement — declares
`independence`, the gate SHALL print one line for each declared rule other
than `reviewer-not-writer`, in the declared order, judging the latest
review of the candidate's commit against the task's implementer sessions —
the session records whose `commit` is one of the candidate's commits,
enumerated over `merge-base..candidate` as the range's writer identities
are. `distinct-vendor` SHALL compare the review's `reviewer.vendor` with
each such session's `usage.provider`; `distinct-model` the review's
`reviewer.model` with each session's `model`; and `distinct-actor` the
review's `reviewer.actor` with each session's `actor` — each side declared
in the project's actors table, a key of the project's `actors` section read
from the same trusted side the contract is read from. A comparison SHALL be
exact string equality after the normalisation the existing identity check
applies — strip and casefold — and a rule SHALL hold only when it holds
against every such session. A session whose compared value equals the
review's SHALL make the rule fail, refusing the candidate with a line
naming the rule, the review's value and the session's value, and every
value a rule line takes from a record SHALL be escaped as the gate's other
lines are.

#### Scenario: a declared rule that holds passes naming the rule
- **WHEN** a contract declares `independence = ['distinct-vendor']` and the
  latest review's `reviewer.vendor` differs from every in-range implementer
  session's `usage.provider`
- **THEN** the transcript carries a `PASS` line for `distinct-vendor`

#### Scenario: a rule failing against one session refuses the candidate
- **WHEN** a contract declares `independence = ['distinct-vendor']` and one
  in-range implementer session's `usage.provider` equals the review's
  `reviewer.vendor`
- **THEN** the gate refuses the candidate with a line naming
  `distinct-vendor`, the review's vendor and the session's vendor

#### Scenario: every in-range implementer session is judged
- **WHEN** two implementer sessions of the task carry commits in the
  candidate's range and the second's `model` equals the latest review's
  `reviewer.model`
- **THEN** `distinct-model` fails against that session though it held
  against the first

#### Scenario: a session outside the candidate's range is not judged
- **WHEN** a session of the task carries a `commit` outside
  `merge-base..candidate`
- **THEN** no declared rule compares against it

#### Scenario: the comparison is case-normalised
- **WHEN** an in-range implementer session's `model` differs from the
  latest review's `reviewer.model` only in letter case
- **THEN** `distinct-model` fails — casing does not evade the check

#### Scenario: the rule lines keep the declared order
- **WHEN** a contract declares `independence = ['distinct-model',
  'distinct-vendor']`
- **THEN** the `distinct-model` line prints before the `distinct-vendor`
  line

#### Scenario: distinct-actor compares declared actors
- **WHEN** a contract declares `distinct-actor`, and the latest review's
  `reviewer.actor` and an in-range implementer session's `actor` are both
  keys of the project's actors table
- **THEN** the rule passes where the two differ and fails where they are
  equal

#### Scenario: the review judged is the latest review of the candidate's commit
- **WHEN** the task carries more than one review of the candidate's commit
- **THEN** the declared rules judge the latest one, as the review check
  does

#### Scenario: values from records are escaped
- **WHEN** a value a rule line prints — the review's or a session's —
  carries a character that could add a line to the output or reorder it
- **THEN** it prints escaped, as the gate's other lines are

#### Scenario: a sidecar's declared rules judge its own journal's records
- **WHEN** a sidecar contract declares `distinct-actor` and the sidecar's
  project file declares the actors
- **THEN** the rule judges the sidecar journal's sessions and review — the
  host's history supplies only the diff and the commit range

### Requirement: A declared rule that cannot be judged reads not checked

Where a declared rule cannot be judged — no implementer session of the
task carries a `commit` in the candidate's range, a compared field is
absent on the review or on a session, or an actor the rule would compare
is not declared in the project's actors table — its line SHALL read
`NOT CHECKED` with the reason: neither a refusal nor a pass.

#### Scenario: no implementer session carries a commit in the range
- **WHEN** no session record of the task carries a `commit` in the
  candidate's range
- **THEN** each declared rule reads `NOT CHECKED` saying so, and the gate
  does not refuse for it

#### Scenario: a compared field absent on the review
- **WHEN** the latest review's `reviewer` object carries no `actor`
- **THEN** `distinct-actor` reads `NOT CHECKED` naming the absent field

#### Scenario: a compared field absent on a session
- **WHEN** an in-range implementer session carries no `model` or no
  `usage.provider`
- **THEN** the rule needing it reads `NOT CHECKED` naming the session and
  the absent field

#### Scenario: a session's actor is not a declared actor
- **WHEN** an in-range implementer session's `actor` is not a key of the
  project's actors table
- **THEN** `distinct-actor` reads `NOT CHECKED` saying the actor is not a
  declared actor

#### Scenario: the review's actor is not a declared actor
- **WHEN** the latest review's `reviewer.actor` is not a key of the
  project's actors table
- **THEN** `distinct-actor` reads `NOT CHECKED` saying so

#### Scenario: a failing session outranks an unjudgeable one
- **WHEN** one in-range implementer session's compared value equals the
  review's and another session's cannot be judged
- **THEN** the rule fails against the judged one — a demonstrated
  violation is reported, never softened by what could not be checked

### Requirement: Without a review the declared rules read not examined

Asked to judge without a review — `review_required` false — and the
candidate carrying no review record, the gate SHALL report each declared
rule as `NOT EXAMINED`, as the existing review-bound checks do; a
candidate that does carry a review SHALL have the rules judged however the
run was asked.

#### Scenario: the declared rules are not examined without a review
- **WHEN** the gate runs with `review_required` false and the candidate
  carries no review record
- **THEN** each declared rule's line reads `NOT EXAMINED` and none counts
  as a violation

#### Scenario: a review is judged however the run was asked
- **WHEN** the gate runs with `review_required` false and the candidate
  carries a review
- **THEN** the declared rules are judged against it as in a normal run

### Requirement: `reviewer-not-writer` is one line and the default transcript is unchanged

`reviewer-not-writer` — the existing declared-identity check — SHALL run
for every candidate exactly as before, whether or not the header names it,
and the header naming it SHALL add no second line. A contract declaring no
`independence` SHALL produce the gate transcript of before byte for byte,
as the pinned default fixtures demonstrate.

#### Scenario: the header naming reviewer-not-writer adds no second line
- **WHEN** a contract declares `independence = ['reviewer-not-writer']`
- **THEN** the transcript carries the existing identity line once and no
  rule line for it

#### Scenario: a contract without independence prints today's transcript
- **WHEN** the contract declares no `independence`
- **THEN** the transcript matches the pinned default byte for byte

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
state; `implementers` and `reviewers` remain declarations later checks
read.

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
