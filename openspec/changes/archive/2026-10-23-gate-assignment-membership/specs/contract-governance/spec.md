## Purpose

The gate's reading of the assignment a schema-3 contract header declares
— `reviewers` and `implementers` — how each membership is judged at the
merge boundary, and what the transcript says where a membership cannot be
judged.

## ADDED Requirements

### Requirement: The gate checks the latest review against the declared reviewers

When the contract the gate reads — the merge-base tree's in the embedded
placement, the sidecar working tree's in the sidecar placement — declares
`reviewers`, the gate SHALL print one line judging the `reviewer.actor`
of the latest review of the candidate's commit — the review the verdict
check judges, whatever its verdict — against the list by exact string
equality, the way `status` compares an actor against a declared list:
actor ids are exact labels, and an actor differing from every declared
entry only in case or surrounding whitespace is not a member. The line
SHALL read `PASS` when the actor is in the list, and `FAIL` — refusing
the candidate, naming the actor and the list — when it is not. A review
carrying no `reviewer.actor` SHALL fail the same line: membership is
what the contract claims, and without an actor it cannot be shown — the
line SHALL say the review is recorded with `--actor` (the operator
decision of 2026-10-23; `review --actor`, CR-182, is the path). The check
is review-bound as the declared independence rules are: asked to judge
without a review — `review_required` false — and the candidate carrying
no review record, the line SHALL read `NOT EXAMINED` with the reason,
and a candidate that does carry a review SHALL have the membership
judged however the run was asked. A contract declaring no `reviewers`
SHALL print no reviewers line. Every value the line takes from a record
or the contract SHALL be escaped as the gate's other lines are.

#### Scenario: a reviewer actor in the declared list passes
- **WHEN** a contract declares `reviewers` and the latest review of the
  candidate's commit carries a `reviewer.actor` that is in the list
- **THEN** the transcript carries a `PASS` line for the declared
  reviewers

#### Scenario: a reviewer outside the list refuses naming the actor and the list
- **WHEN** a contract declares `reviewers` and the latest review's
  `reviewer.actor` is not in the list
- **THEN** the gate refuses the candidate with a `FAIL` line naming the
  actor and the declared reviewers

#### Scenario: reviewer membership compares actor ids exactly
- **WHEN** a contract declares `reviewers` and the latest review's
  `reviewer.actor` differs from every declared entry — though it equals
  one but for letter case
- **THEN** the line fails — actor ids are exact labels and case does not
  make a member

#### Scenario: a review carrying no actor refuses naming the --actor path
- **WHEN** a contract declares `reviewers` and the latest review's
  `reviewer` object carries no `actor`
- **THEN** the gate refuses the candidate with a `FAIL` line saying the
  review is recorded with `--actor`

#### Scenario: the review judged is the latest whatever its verdict
- **WHEN** a contract declares `reviewers` and the latest review of the
  candidate's commit is non-approving
- **THEN** the reviewers line still judges that review's
  `reviewer.actor` against the list

#### Scenario: without a review the reviewers line reads not examined
- **WHEN** the gate runs with `review_required` false, the contract
  declares `reviewers`, and the candidate carries no review record
- **THEN** the reviewers line reads `NOT EXAMINED` with the reason, as
  the other review-bound lines do

#### Scenario: a review's membership is judged however the run was asked
- **WHEN** the gate runs with `review_required` false, the contract
  declares `reviewers`, and the candidate carries a review
- **THEN** the reviewers line judges that review's `reviewer.actor`
  against the list as in a normal run

#### Scenario: a contract declaring no reviewers prints no reviewers line
- **WHEN** the contract declares `implementers` or `independence` but no
  `reviewers`
- **THEN** the transcript carries no reviewers line

### Requirement: The gate checks the in-range implementer sessions against the declared implementers

When the contract the gate reads declares `implementers`, the gate SHALL
print one line judging the `actor` of every implementer session of the
task whose `commit` is in the candidate's `merge-base..candidate` range —
the same sessions the declared independence rules judge — against the
list by exact string equality. The line SHALL read `PASS` when every
in-range session's actor is in the list, and `FAIL` — refusing the
candidate, naming each session whose actor is not — when any is not.
When no implementer session of the task carries a `commit` in the range
the line SHALL read `NOT CHECKED` with the reason: neither a refusal nor
a pass — a provider's CI run can hold no session yet. The check is not
review-bound: it is judged however the run was asked, with a review or
without one. A contract declaring no `implementers` SHALL print no
implementers line. Every value the line takes from a record or the
contract SHALL be escaped as the gate's other lines are.

#### Scenario: every in-range implementer session's actor in the list passes
- **WHEN** a contract declares `implementers` and every implementer
  session whose `commit` is in the candidate's range carries an `actor`
  in the list
- **THEN** the transcript carries a `PASS` line for the declared
  implementers

#### Scenario: a session outside the list refuses naming the session and actor
- **WHEN** a contract declares `implementers` and one in-range
  implementer session's `actor` is not in the list
- **THEN** the gate refuses the candidate with a `FAIL` line naming the
  session and its actor

#### Scenario: each offending session is named
- **WHEN** two in-range implementer sessions carry actors outside the
  declared `implementers`
- **THEN** the `FAIL` line names each of them

#### Scenario: implementer membership compares actor ids exactly
- **WHEN** a contract declares `implementers` and an in-range implementer
  session's `actor` differs from every declared entry — though it equals
  one but for letter case
- **THEN** the line fails — actor ids are exact labels and case does not
  make a member

#### Scenario: a session outside the range is not judged for membership
- **WHEN** a contract declares `implementers` and a session of the task
  carries a `commit` outside `merge-base..candidate` whose `actor` is not
  in the list
- **THEN** the membership line does not judge it

#### Scenario: no in-range implementer session reads not checked
- **WHEN** a contract declares `implementers` and no implementer session
  of the task carries a `commit` in the candidate's range
- **THEN** the implementers line reads `NOT CHECKED` with the reason —
  neither a refusal nor a pass

#### Scenario: the implementers line is judged however the run was asked
- **WHEN** the gate runs with `review_required` false, the contract
  declares `implementers`, and an implementer session's `commit` is in
  the candidate's range
- **THEN** the implementers line judges the session's `actor` against
  the list as in a normal run

#### Scenario: a contract declaring no implementers prints no implementers line
- **WHEN** the contract declares `reviewers` or `independence` but no
  `implementers`
- **THEN** the transcript carries no implementers line

#### Scenario: values the membership lines print are escaped
- **WHEN** a value a membership line prints — a declared list entry or an
  actor a record carries — carries a character that could add a line to
  the output or reorder it
- **THEN** it prints escaped, as the gate's other lines are

### Requirement: A contract declaring neither list changes no transcript

A contract whose header declares neither `reviewers` nor `implementers`
SHALL produce the gate transcript of before, byte for byte, in every
placement and on every lane — the pinned default fixtures demonstrate
it.

#### Scenario: a contract declaring neither list prints today's transcript
- **WHEN** the contract declares neither `reviewers` nor `implementers`
- **THEN** the transcript matches the pinned default byte for byte

## MODIFIED Requirements

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
from the same trusted side the contract is read from. A `distinct-vendor`
or `distinct-model` comparison SHALL be exact string equality after the
normalisation the existing identity check applies — strip and casefold —
and a `distinct-actor` comparison SHALL be exact string equality alone:
actor ids are exact labels, the keys of the project's actors table and the
entries of the declared lists, which `status` compares exactly — a pair of
actor ids differing only in case is a pair of different declared actors. A
rule SHALL hold only when it holds
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

#### Scenario: distinct-actor compares actor ids exactly
- **WHEN** a contract declares `distinct-actor`, and the latest review's
  `reviewer.actor` and an in-range implementer session's `actor` are keys
  of the project's actors table that differ only in letter case
- **THEN** the rule passes — two actor ids differing only in case are two
  different declared actors

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
