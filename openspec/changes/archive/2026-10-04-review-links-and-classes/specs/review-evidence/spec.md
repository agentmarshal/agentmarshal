## ADDED Requirements

### Requirement: A review may name the task's previous review
From schema 7 a review record MAY carry `previous_review` — the id of
the task's previous review (ADR-0016 decision 2), a record id in the
form record ids take: a 26-character Crockford base32 ULID. The field
SHALL pass the forgeable-text rule registered for the review record
type and field. Nothing resolves the id against the journal at the
record layer — what it points at is the writer's.

#### Scenario: a review carrying previous_review is written and read back
- **WHEN** a review record carries `previous_review` naming a record id
- **THEN** it is written and validated, and the field reads back as given

#### Scenario: a previous_review that is not a record id is refused
- **WHEN** a review record's `previous_review` is not a string in the
  form record ids take, or not a string at all
- **THEN** it is refused and nothing is written

#### Scenario: a previous_review that could forge a line is refused
- **WHEN** a review record's `previous_review` carries a character that
  could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: A review may carry a class for each of its findings
From schema 7 a review record MAY carry `classes` — an object whose
every key is a finding id the same record names in `findings` or
`advisory_findings` and whose every value is a non-empty string, the
finding's class (ADR-0016 decision 3). Each class value SHALL pass the
forgeable-text rule. A class outside the project's vocabulary SHALL NOT
be refused by the record — recording it as `other` is the writer's. An
empty `classes` object SHALL be refused: a review with nothing
classified carries no `classes`.

#### Scenario: a review carrying classes for its findings is written and read back
- **WHEN** a review record carries `classes` whose keys name finding
  ids of its `findings` and `advisory_findings` and whose values are
  non-empty strings
- **THEN** it is written and validated, and the field reads back as
  given

#### Scenario: a class outside the project's vocabulary is admitted
- **WHEN** a review record carries `classes` naming a class the
  project's vocabulary does not know
- **THEN** the record is admitted — mapping it to `other` is the
  writer's, not the record's

#### Scenario: a classes key naming no finding of the record is refused
- **WHEN** a review record's `classes` carries a key that is not a
  finding id in the record's `findings` or `advisory_findings`
- **THEN** it is refused and nothing is written

#### Scenario: an empty classes object is refused
- **WHEN** a review record carries `classes` as an empty object
- **THEN** it is refused and nothing is written

#### Scenario: a classes that is not an object is refused
- **WHEN** a review record's `classes` is not an object
- **THEN** it is refused and nothing is written

#### Scenario: a class value that is empty or not a string is refused
- **WHEN** a review record's `classes` carries a value that is empty,
  all whitespace or not a string
- **THEN** it is refused and nothing is written

#### Scenario: a class value that could forge a line is refused
- **WHEN** a review record's `classes` carries a value holding a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The reviewer object may carry the reviewer's declared actor
From schema 7 a review record's `reviewer` object MAY carry `actor` —
a non-empty string, the declared reviewer actor the distinct-actor rule
compares (ADR-0018 decision 3) — which SHALL pass the forgeable-text
rule; the object stays closed to every other key. Below schema 7 the
object SHALL stay exactly `role`, `vendor`, `model`, `email`.

#### Scenario: a review whose reviewer carries actor is written and read back
- **WHEN** a review record's `reviewer` carries `actor` as a non-empty
  string
- **THEN** it is written and validated, and the key reads back as given

#### Scenario: an actor that is empty or not a string is refused
- **WHEN** a review record's `reviewer.actor` is empty, all whitespace
  or not a string
- **THEN** it is refused and nothing is written

#### Scenario: an actor that could forge a line is refused
- **WHEN** a review record's `reviewer.actor` carries a character that
  could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: the reviewer object stays closed to any other key
- **WHEN** a review record's `reviewer` carries a key that is not
  `role`, `vendor`, `model`, `email` or `actor`
- **THEN** it is refused and nothing is written

### Requirement: The link, the classes and the reviewer actor are fields of schema 7
A review record carrying `previous_review`, `classes` or
`reviewer.actor` SHALL carry schema 7: a writer carrying any of them
SHALL stamp 7 through the minimum-schema derivation — `reviewer.actor`,
a key of the reviewer object, raising the stamp the same. None SHALL be
admitted to a review stamped below 7, refused at write and on read —
the two top-level fields by the field-admission rule of the record's
own schema, `actor` by the reviewer object's closed keys under the
record's own schema. A review carrying none of them SHALL be validated
and stamped exactly as before, and the fields SHALL be declared through
the registrations the schema-7 record types use — the field family, the
shared validator tables and the minimum-schema derivation — not by a
second mechanism.

#### Scenario: a review carrying a field of the family stamps schema 7
- **WHEN** a review record is built carrying `previous_review`,
  `classes` or `reviewer.actor`
- **THEN** it carries schema 7

#### Scenario: a field of the family on a review below schema 7 is refused at write
- **WHEN** a review record stamped below 7 carries `previous_review`,
  `classes` or `reviewer.actor`
- **THEN** it is refused and nothing is written

#### Scenario: a field of the family on a review below schema 7 is refused on read
- **WHEN** the journal holds a review record stamped below 7 that
  carries `previous_review`, `classes` or `reviewer.actor`
- **THEN** reading the task's records refuses it

#### Scenario: a review carrying none of the fields keeps its schema and reads as before
- **WHEN** a review record carries none of `previous_review`, `classes`
  and `reviewer.actor`
- **THEN** it is validated and stamped exactly as before the family
  existed
