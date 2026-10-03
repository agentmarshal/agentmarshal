## ADDED Requirements

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
no task state and is not admitted after a terminal record. Nothing reads
acknowledgements yet — the command that writes them and the surfaces that
mark acknowledged hits come with their own tasks.

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

### Requirement: An acknowledgement record is a record of schema 7
An `acknowledgement` record SHALL carry schema 7 — the schema the record
type was introduced under. An `acknowledgement` record stamped below 7
SHALL be refused at write, and on read: the field-admission rule of the
record's own schema admits the family's fields only from 7, and the
record-type gate refuses the type below its schema whatever the record
carries. A writer SHALL stamp 7 through the minimum-schema derivation — the
record type itself needs it.

#### Scenario: an acknowledgement record stamps schema 7
- **WHEN** an `acknowledgement` record is built
- **THEN** it carries schema 7

#### Scenario: an acknowledgement record stamped below 7 is refused at write
- **WHEN** an `acknowledgement` record stamped below 7 is presented for
  write
- **THEN** it is refused and nothing is written

#### Scenario: an acknowledgement record stamped below 7 is refused on read
- **WHEN** the journal holds an `acknowledgement` record stamped below 7
- **THEN** reading the task's records refuses it
