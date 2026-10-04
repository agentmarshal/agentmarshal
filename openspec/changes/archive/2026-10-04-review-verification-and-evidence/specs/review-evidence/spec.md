## ADDED Requirements

### Requirement: A review may carry what it executed and read
From schema 7 a review record MAY carry `verification` — what the
reviewer ran, read and could not run (ADR-0017 decision 4, ADR-0022
section 2): an object with one or more of the keys `executed`, `read`
and `not_run` and no other key, `executed` a non-empty array of objects
carrying exactly `what` and `result`, `read` a non-empty array of
strings, and `not_run` a non-empty array of objects carrying exactly
`what` and `why`. Every string inside SHALL be non-empty and SHALL pass
the forgeable-text rule, and a refusal SHALL name the key and the
position at fault.

#### Scenario: a review carrying verification is written and read back
- **WHEN** a review record carries `verification` naming what was
  executed, what was read and what was not run
- **THEN** it is written and validated, and the field reads back as
  given

#### Scenario: a verification that is not an object is refused
- **WHEN** a review record's `verification` is not an object
- **THEN** it is refused and nothing is written

#### Scenario: an empty verification object is refused
- **WHEN** a review record carries `verification` as an empty object
- **THEN** it is refused and nothing is written

#### Scenario: a verification carrying a key outside the three is refused
- **WHEN** a review record's `verification` carries a key that is not
  `executed`, `read` or `not_run`
- **THEN** it is refused and nothing is written

#### Scenario: a verification section that is not a non-empty array is refused
- **WHEN** a review record's `verification` carries `executed`, `read`
  or `not_run` as an empty array or as a value that is not an array
- **THEN** it is refused and nothing is written

#### Scenario: an executed entry missing a key or carrying another is refused
- **WHEN** a review record's `verification.executed` carries an entry
  that is not an object carrying exactly `what` and `result`
- **THEN** it is refused and nothing is written

#### Scenario: a not_run entry missing a key or carrying another is refused
- **WHEN** a review record's `verification.not_run` carries an entry
  that is not an object carrying exactly `what` and `why`
- **THEN** it is refused and nothing is written

#### Scenario: a verification string that is empty or not a string is refused
- **WHEN** a string inside a review record's `verification` — a `read`
  item, or an entry's `what`, `result` or `why` — is empty, all
  whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a verification string that could forge a line is refused
- **WHEN** a string inside a review record's `verification` carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a refusal names the key and the position at fault
- **WHEN** a review record's `verification` is refused
- **THEN** the refusal names the section, the position and the key at
  fault

### Requirement: A review may carry evidence for its findings
From schema 7 a review record MAY carry `evidence` — a non-empty object
whose every key is a finding id the same record names in `findings` or
`advisory_findings` and whose every value is a non-empty string, the
evidence behind the finding (ADR-0017 decision 5): a link, a
`file:line`, or the command that checked the claim with the essential
part of its output. Each value SHALL pass the forgeable-text rule, and
each refusal SHALL name the key at fault. An empty `evidence` object
SHALL be refused: a review with no evidence to name carries no
`evidence`.

#### Scenario: a review carrying evidence for its findings is written and read back
- **WHEN** a review record carries `evidence` whose keys name finding
  ids of its `findings` and `advisory_findings` and whose values are
  non-empty strings
- **THEN** it is written and validated, and the field reads back as
  given

#### Scenario: an evidence key naming no finding of the record is refused
- **WHEN** a review record's `evidence` carries a key that is not a
  finding id in the record's `findings` or `advisory_findings`
- **THEN** it is refused and nothing is written

#### Scenario: an empty evidence object is refused
- **WHEN** a review record carries `evidence` as an empty object
- **THEN** it is refused and nothing is written

#### Scenario: an evidence that is not an object is refused
- **WHEN** a review record's `evidence` is not an object
- **THEN** it is refused and nothing is written

#### Scenario: an evidence value that is empty or not a string is refused
- **WHEN** a review record's `evidence` carries a value that is empty,
  all whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: an evidence value that could forge a line is refused
- **WHEN** a review record's `evidence` carries a value holding a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The verification and the evidence are fields of schema 7
A review record carrying `verification` or `evidence` SHALL carry schema
7: a writer carrying either SHALL stamp 7 through the minimum-schema
derivation. Neither SHALL be admitted to a review stamped below 7,
refused at write and on read by the field-admission rule of the record's
own schema. A review carrying neither SHALL be validated and stamped
exactly as before, and the fields SHALL be declared through the
registrations the schema-7 record types use — the field family, the
shared validator tables and the minimum-schema derivation — not by a
second mechanism.

#### Scenario: a review carrying either field stamps schema 7
- **WHEN** a review record is built carrying `verification` or
  `evidence`
- **THEN** it carries schema 7

#### Scenario: either field on a review below schema 7 is refused at write
- **WHEN** a review record stamped below 7 carries `verification` or
  `evidence`
- **THEN** it is refused and nothing is written

#### Scenario: either field on a review below schema 7 is refused on read
- **WHEN** the journal holds a review record stamped below 7 that
  carries `verification` or `evidence`
- **THEN** reading the task's records refuses it

#### Scenario: a review carrying neither field keeps its schema and reads as before
- **WHEN** a review record carries neither `verification` nor `evidence`
- **THEN** it is validated and stamped exactly as before the fields
  existed
