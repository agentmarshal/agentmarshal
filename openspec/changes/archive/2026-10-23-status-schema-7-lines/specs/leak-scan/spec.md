## ADDED Requirements

### Requirement: `status` shows an acknowledgement record on a line of its own

`agentmarshal status <task>` SHALL print one line per `acknowledgement`
record — after the record's id, type and time: the acknowledged commit's
short form, the `file` as recorded, the hit's identification — the
`signature` when the record carries one, the `marker`'s number when it
carries a marker — and the `reason` — and SHALL name the recorder. A
recorder that is not a declared actor SHALL be shown as not a declared
actor. Where the recorder is a declared author or committer of the
acknowledged commit the line SHALL say the hit was self-acknowledged —
derived on display the way the self-acceptance mark is, never stored —
and where git cannot read the commit the line SHALL say the mark was not
checked rather than answering either way. Every value taken from the
record SHALL be escaped on display as the other record lines' values are.

#### Scenario: status shows an acknowledgement's line
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record carrying a `signature`
- **THEN** its line carries the commit's short form, `file`,
  `signature`, `recorded_by` and `reason`

#### Scenario: a marker's number identifies the hit on the line
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record carrying a `marker`
- **THEN** its line carries `marker` and the marker's number, and no
  `signature`

#### Scenario: a self-acknowledgement is marked
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose recorder is a declared author or committer of the
  acknowledged commit
- **THEN** the line says the hit was self-acknowledged

#### Scenario: an acknowledgement by another actor is not marked
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose recorder is not a declared author or committer of the
  acknowledged commit
- **THEN** the line carries no self-acknowledgement mark

#### Scenario: git cannot read the commit
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose commit git cannot read
- **THEN** the line says the self-acknowledgement mark was not checked

#### Scenario: a recorder that is not a declared actor is shown as such
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose `recorded_by` is not a declared actor
- **THEN** the line names the recorder and says it is not a declared
  actor

#### Scenario: an acknowledgement's values stay on their own line
- **WHEN** `agentmarshal status <task>` lists an `acknowledgement`
  record whose `file`, `reason`, `signature` or `recorded_by` carries a
  character that could add a line to rendered output or reorder it — a
  value an older schema's journal can hold where today's read rules do
  not reach
- **THEN** each refused character prints as its escape and the record
  stays on the one line

## MODIFIED Requirements

### Requirement: An acknowledgement record carries a reviewed leak-scan hit
From schema 7 the journal admits an `acknowledgement` record: what an
operator writes having verified that a hit the added-content scan reported
is not a leak (ADR-0021). The record SHALL carry `commit` — the candidate
commit the hit was found in, exactly 40 lowercase hex characters; `file` —
the file exactly as the scan's hit prints it, a path already masked, a
non-empty string; exactly one of `signature` — the identifier of a built-in
signature the scan knows — and `marker` — the matched marker's position in
the project's configured marker list, an integer of at least 1 — the hit's
identification as the scan prints it, never the matched text and never the
marker's value; and `reason` — a non-empty string of at most 1000
characters, bounded by the character-bounded text rule. `file` and `reason`
SHALL pass the forgeable-text rule registered for this record type and
field. The record SHALL name its recorder in `recorded_by` with
`recorded_by_source`, as `finding` and `check` already do. It projects to
no task state and is not admitted after a terminal record. `status` is the
surface that reads it — the command that writes acknowledgements and the
hit surfaces that mark acknowledged hits come with their own tasks.

#### Scenario: an acknowledgement record is written and read back
- **WHEN** an `acknowledgement` record carries `commit`, `file`,
  `signature` and `reason`
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: a marker's position identifies the hit as well
- **WHEN** an `acknowledgement` record carries `marker` in place of
  `signature`
- **THEN** it is written and validated, and `signature` appears nowhere in
  it

#### Scenario: a record carrying both or neither of signature and marker is refused
- **WHEN** an `acknowledgement` record carries both `signature` and
  `marker`, or neither
- **THEN** it is refused with a refusal naming the two fields, and nothing
  is written

#### Scenario: a signature the scan does not know is refused
- **WHEN** an `acknowledgement` record's `signature` is not a string or not
  the identifier of a built-in signature the scan knows
- **THEN** it is refused and nothing is written

#### Scenario: a marker that is not an integer of at least 1 is refused
- **WHEN** an `acknowledgement` record's `marker` is not an integer, or is
  an integer below 1
- **THEN** it is refused and nothing is written

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** an `acknowledgement` record's `commit` is missing, not a string,
  or not exactly 40 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: a file that is missing or empty is refused
- **WHEN** an `acknowledgement` record's `file` is missing, empty, all
  whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a reason that is missing or empty is refused
- **WHEN** an `acknowledgement` record's `reason` is missing, empty, all
  whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a reason beyond the character bound is refused
- **WHEN** an `acknowledgement` record's `reason` carries more than 1000
  characters
- **THEN** it is refused and nothing is written

#### Scenario: a displayed string that could forge a line is refused
- **WHEN** an `acknowledgement` record's `file` or `reason` carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: an acknowledgement record that names no recorder is refused
- **WHEN** an `acknowledgement` record carries neither `recorded_by` nor
  `recorded_by_source`
- **THEN** it is refused

#### Scenario: an acknowledgement on a closed task is refused
- **WHEN** an `acknowledgement` record is written for a task that has
  completed or been abandoned
- **THEN** no record is written, the refusal names the state, and the
  journal still validates
