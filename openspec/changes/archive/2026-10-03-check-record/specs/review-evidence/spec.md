## ADDED Requirements

### Requirement: A check record carries what a pipeline check found on a commit
From schema 7 the journal admits a `check` record: a trace of what a
pipeline check found on a commit, written by whoever observed the run —
a measurement that projects to no task state and that the gate decides
nothing from. The record SHALL carry `commit` — exactly 40 lowercase hex
characters; `name` — a non-empty string naming the check; and `result` —
one of `passed`, `failed`, `error` or `skipped`. It MAY carry
`failed_step`, `excerpt` and `run_url`, each a non-empty string when
present. `excerpt` SHALL be bounded at 4 KiB of UTF-8 by the byte-bounded
text rule — refused beyond, never truncated by the record layer — and
`name`, `failed_step`, `excerpt` and `run_url` SHALL pass the
forgeable-text rule registered for this record type and field. A `check`
record SHALL name its recorder in `recorded_by` with
`recorded_by_source`, as `finding` already does.

#### Scenario: a check record is written and read back
- **WHEN** a `check` record carries `commit`, `name`, `result` and all
  three optional fields
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: the optional fields may be absent
- **WHEN** a `check` record carries only the required fields
- **THEN** it is written and validated, and none of `failed_step`,
  `excerpt` or `run_url` appears in it

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** a `check` record's `commit` is missing, not a string, or not
  exactly 40 lowercase hex characters
- **THEN** it is refused and nothing is written

#### Scenario: a name that is missing or empty is refused
- **WHEN** a `check` record's `name` is missing, empty, all whitespace
  or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a result outside the outcome vocabulary is refused
- **WHEN** a `check` record's `result` is missing, not a string, or not
  one of `passed`, `failed`, `error` or `skipped`
- **THEN** it is refused and nothing is written

#### Scenario: an optional field that is empty is refused
- **WHEN** a `check` record's `failed_step`, `excerpt` or `run_url` is
  present but empty, all whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: an excerpt beyond the byte bound is refused
- **WHEN** a `check` record's `excerpt` encodes to more than 4 KiB of
  UTF-8
- **THEN** it is refused and nothing is written

#### Scenario: a displayed string that could forge a line is refused
- **WHEN** a `check` record's `name`, `failed_step`, `excerpt` or
  `run_url` carries a character that could add a line to rendered output
  or reorder it
- **THEN** the record is refused

#### Scenario: a check record that names no recorder is refused
- **WHEN** a `check` record carries neither `recorded_by` nor
  `recorded_by_source`
- **THEN** it is refused

### Requirement: A check record is a record of schema 7
A `check` record SHALL carry schema 7 — the schema the record type was
introduced under. A `check` record stamped below 7 SHALL be refused at
write, and on read: the field-admission rule of the record's own schema
admits the family's fields only from 7, and the record-type gate refuses
the type below its schema whatever the record carries. A writer SHALL
stamp 7 through the minimum-schema derivation — the record type itself
needs it.

#### Scenario: a check record stamps schema 7
- **WHEN** a `check` record is built
- **THEN** it carries schema 7

#### Scenario: a check record stamped below 7 is refused at write
- **WHEN** a `check` record stamped below 7 is presented for write
- **THEN** it is refused and nothing is written

#### Scenario: a check record stamped below 7 is refused on read
- **WHEN** the journal holds a `check` record stamped below 7
- **THEN** reading the task's records refuses it
