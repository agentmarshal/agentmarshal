## ADDED Requirements

### Requirement: Both review paths take the reviewer's declared actor
`agentmarshal submit-review` and `agentmarshal review` — the launcher in
its commit form and its finding-review form — SHALL take an optional
`--actor <id>` naming the declared reviewer actor (ADR-0018 decision 3,
ADR-0022 section 2). When given, the review record's `reviewer` object
SHALL carry `actor` with that value, passed through
`create_review_record`'s `reviewer_actor` parameter, and the record
SHALL stamp schema 7 through the minimum-schema derivation. The value
SHALL be the flag's own: it SHALL NOT be derived from the environment or
the git identity — the process that launches a reviewer is usually not
the reviewer — and it SHALL stay independent of `recorded_by`, which
says who wrote the record and stamps as before.

#### Scenario: submit-review --actor records the reviewer actor
- **WHEN** `submit-review` records a verdict given `--actor <id>`
- **THEN** the review record's `reviewer` object carries `actor` with
  that value and the record stamps schema 7

#### Scenario: review --actor records the reviewer actor on a commit review
- **WHEN** `review` records a commit verdict given `--actor <id>`
- **THEN** the review record's `reviewer` object carries `actor` with
  that value and the record stamps schema 7

#### Scenario: review --actor records the reviewer actor on a finding review
- **WHEN** `review --reviewed-finding` records a verdict given
  `--actor <id>`
- **THEN** the review record's `reviewer` object carries `actor` with
  that value and the record stamps schema 7

#### Scenario: the reviewer actor is not confused with recorded_by
- **WHEN** a review is recorded given `--actor` by a recorder resolving
  a different actor
- **THEN** the record keeps both — `recorded_by` the writer,
  `reviewer.actor` the declared reviewer actor

### Requirement: Without --actor the review paths are unchanged
Without `--actor` both paths SHALL write the same record, stamp the same
schema and print the same lines as before the flag existed: the flag
adds a capability, never an obligation.

#### Scenario: a review written without --actor is byte-for-byte as before
- **WHEN** `submit-review` or `review` records a verdict without
  `--actor`
- **THEN** the record — apart from its id and times — is byte-for-byte
  the record the command wrote before the flag existed, and every line
  the command prints is unchanged

### Requirement: A refused --actor costs nothing
Each path SHALL check `--actor` against the record's own rule — a
non-empty string carrying no character that could forge a line — before
anything is written and, for the launcher, before the reviewer command
starts; the refusal SHALL name `--actor`.

#### Scenario: submit-review refuses a refused actor value before writing
- **WHEN** `submit-review --actor` is empty, all whitespace or carries a
  character that could forge a line
- **THEN** the command refuses naming `--actor`, and nothing is written

#### Scenario: the launcher refuses a refused actor value before the reviewer runs
- **WHEN** `review --actor` is empty, all whitespace or carries a
  character that could forge a line
- **THEN** the command refuses naming `--actor` before the reviewer
  command is invoked, and nothing is written

#### Scenario: the dry run refuses a refused actor value before the reviewer runs
- **WHEN** `review --dry-run --actor` is empty, all whitespace or carries
  a character that could forge a line
- **THEN** the command refuses naming `--actor` before the reviewer
  command is invoked, and nothing is written

### Requirement: An undeclared reviewer actor is accepted and noted
An `--actor` id that is not in the project's actors table SHALL be
accepted and recorded as given — the record stands, as an undeclared
recorder does (ADR-0022 section 3) — and the command SHALL say the id is
not a declared actor. Declared-ness SHALL be tested on the id against
the `actors` keys of the project file of the repository holding the
journal — the same project `recorded_by` resolves from.

#### Scenario: an undeclared reviewer actor is accepted and noted
- **WHEN** `--actor` names an id the project's actors table does not
  declare
- **THEN** the review is recorded with the actor as given, and the
  command says the actor is not a declared actor

#### Scenario: a declared reviewer actor is recorded with no note
- **WHEN** `--actor` names an id the project's actors table declares
- **THEN** the review is recorded and no not-declared note is printed

### Requirement: --dry-run shows the actor it would record
`--actor` SHALL be admitted beside `review --dry-run` — the one record
flag the dry run accepts — and a dry run carrying it SHALL say which
actor a recorded review would carry, with the same not-declared note a
recorded run prints.

#### Scenario: a dry run shows the actor it would record
- **WHEN** `review --dry-run --actor <id>` runs
- **THEN** the command's report of the dry run names the actor a
  recorded review would carry

#### Scenario: a dry run notes an undeclared actor as a recorded run does
- **WHEN** `review --dry-run --actor` names an id the project's actors
  table does not declare
- **THEN** the command shows the actor it would record and notes the id
  is not a declared actor
