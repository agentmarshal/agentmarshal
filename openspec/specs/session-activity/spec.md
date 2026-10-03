# session-activity Specification

## Purpose
What a session record can say about the kind of work it measures. An
activity vocabulary that has no word for the most expensive role in an
agent-driven loop turns three quarters of a task's cost into "other", which is
not accounting.

## Requirements

### Requirement: A session can be recorded as coordination
A session record SHALL accept `coordination` as its activity, beside
`implementation`, `review` and `other`: the work of the agent that writes the
contract, launches the implementer, reads the verdict and reports to the
operator. The vocabulary SHALL be defined once and read by every writer and
reader of session records.

#### Scenario: a coordinating session is recorded as such
- **WHEN** a session is recorded with the activity `coordination`
- **THEN** the record is written and validated, and its activity reads back as
  `coordination`

#### Scenario: an activity outside the vocabulary is still refused
- **WHEN** a session is recorded with an activity that is not in the
  vocabulary
- **THEN** it is refused and nothing is written

### Requirement: An older reader refuses a coordination session by its schema
A session record whose activity is `coordination` SHALL carry at least the
schema number that introduced the value — 6 — and 7 when it carries a field
of the schema-7 session family, and a record with any other activity SHALL
keep the schema it had unless a field of the schema-7 session family raises
it to 7. A reader that predates the value then refuses the record as an
unsupported schema rather than as a malformed field, and a journal that never
records coordination stays readable by it.

#### Scenario: coordination stamps the newer schema
- **WHEN** a session is recorded with the activity `coordination` carrying
  none of the schema-7 session fields
- **THEN** the record carries schema 6, the newer schema number the value
  introduced

#### Scenario: a coordination session carrying a schema-7 field carries 7
- **WHEN** a session is recorded with the activity `coordination` carrying
  a field of the schema-7 session family
- **THEN** the record carries schema 7

#### Scenario: other activities keep their schema
- **WHEN** a session is recorded with `implementation`, `review` or `other`
  carrying none of the schema-7 session fields
- **THEN** the record carries the same schema number as before this change

#### Scenario: a non-coordination session carrying a schema-7 field carries 7
- **WHEN** a session is recorded with `implementation`, `review` or `other`
  carrying a field of the schema-7 session family
- **THEN** the record carries schema 7

### Requirement: A session record can say what it produced and with what
From schema 7, a session record MAY carry `commit` — the commit the
implementer run produced, as exactly 40 lowercase hex characters; `model`
— a non-empty string naming the model the session ran; `trace` — a
non-empty string holding an external link to the run's trace, recorded and
never fetched; `cli_session` — a non-empty string naming the CLI session a
resume needs; `report_ready` — a boolean saying the run's report was
finished; and `fallback_reason` — a non-empty string saying why a run
moved down the fallback list, shown and never verified. Each field is
optional. Each of `commit`, `model`, `trace`, `cli_session` and
`fallback_reason` SHALL pass the forgeable-text rule registered for the
session record type and that field, and no length bound SHALL apply to
any of them.

#### Scenario: a session carrying the new fields is written and read back
- **WHEN** a session record carries `commit`, `model`, `trace`,
  `cli_session`, `report_ready` and `fallback_reason`
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: each new field is optional
- **WHEN** a session record carries none of the family's fields
- **THEN** it is written and validated, and none of them appears in it

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** a session record's `commit` is not exactly 40 lowercase hex
  characters
- **THEN** it is refused and nothing is written

#### Scenario: an empty string field is refused
- **WHEN** a session record's `model`, `trace`, `cli_session` or
  `fallback_reason` is empty, all whitespace or is not a string
- **THEN** it is refused and nothing is written

#### Scenario: a report_ready that is not a boolean is refused
- **WHEN** a session record's `report_ready` is not a boolean
- **THEN** it is refused and nothing is written

#### Scenario: a string field that could forge a rendered line is refused
- **WHEN** a string field of the family carries a character that could add
  a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The schema-7 session fields are refused below schema 7
A session record carrying any of `commit`, `model`, `trace`,
`cli_session`, `report_ready` or `fallback_reason` SHALL carry schema 7:
a writer carrying any of them stamps schema 7 through the minimum-schema
derivation, and none of the fields SHALL be admitted to a session record
stamped below 7 — refused at write, and on read by the field-admission
rule of the record's own schema, as every schema-gated field is. A session
record carrying none of them SHALL stamp the schema it stamps without the
family: 3, or 6 for a coordination activity.

#### Scenario: a session carrying a field of the family stamps schema 7
- **WHEN** a session is recorded carrying any of the family's fields
- **THEN** the record carries schema 7

#### Scenario: a field of the family on a session below schema 7 is refused at write
- **WHEN** a session record stamped below 7 carries a field of the family
- **THEN** it is refused and nothing is written

#### Scenario: a field of the family on a session below schema 7 is refused on read
- **WHEN** the journal holds a session record stamped below 7 that carries
  a field of the family
- **THEN** reading the task's records refuses it as an unsupported field

#### Scenario: a session without the family keeps its schema
- **WHEN** a session is recorded carrying none of the family's fields
- **THEN** it carries the schema it carried before the family existed —
  3, or 6 for a `coordination` activity
