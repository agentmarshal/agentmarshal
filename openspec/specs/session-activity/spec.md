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
A session record whose activity is `coordination` SHALL carry the schema number
that introduced the value, and a record with any other activity SHALL keep the
schema it had. A reader that predates the value then refuses the record as an
unsupported schema rather than as a malformed field, and a journal that never
records coordination stays readable by it.

#### Scenario: coordination stamps the newer schema
- **WHEN** a session is recorded with the activity `coordination`
- **THEN** the record carries the newer schema number

#### Scenario: other activities keep their schema
- **WHEN** a session is recorded with `implementation`, `review` or `other`
- **THEN** the record carries the same schema number as before this change
