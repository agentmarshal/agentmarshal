# finding-lifecycle Specification

## Purpose
The lifecycle ADR-0016 gives a review's findings. A blocking finding is
answered by the work or by an operator acceptance; an advisory finding
blocks nothing and overrides nothing — but it is no longer met with
silence. For the review the gate passed on, completion takes a recorded
disposition for each of that review's advisory findings — `fixed`;
`deferred`, with a reason, optionally naming a follow-up task; or
`rejected`, with a reason — and records them in the `completed` record,
so an approval is never a silence about known defects and a deferral
stays visible after the task closes. The findings lane is untouched by
this: `complete --findings` takes no dispositions. This capability
begins with the field that carries the dispositions; the command that
takes them, its refusal when one is missing, and the views that show
open deferrals extend it in later tasks.

## Requirements

### Requirement: A completed record may carry the dispositions of the review's advisory findings
From schema 7 a `completed` record bound by `completed_commit` MAY carry
`advisory_dispositions` — a non-empty object whose every key SHALL be a
non-empty finding id passing the rule finding ids pass — a non-empty
string carrying no character that could forge a line — and whose every
value SHALL be a disposition object. A disposition object SHALL carry
`disposition`, one of `fixed`, `deferred` and `rejected`; `reason`, a
non-empty string passing the forgeable-text rule, required on `deferred`
and `rejected` and optional on `fixed`; and `follow_up`, a task id in
the form task ids take passing the forgeable-text rule, admitted on
`deferred` only. No other key SHALL be admitted, and each refusal SHALL
name the finding id and the key at fault.

#### Scenario: a completed record carrying advisory dispositions is written and read back
- **WHEN** a `completed` record bound by `completed_commit` carries
  `advisory_dispositions` whose keys are finding ids and whose values
  are well-formed disposition objects
- **THEN** it is written and validated, and the field reads back as given

#### Scenario: an advisory_dispositions that is not an object is refused
- **WHEN** a `completed` record's `advisory_dispositions` is not an
  object
- **THEN** it is refused and nothing is written

#### Scenario: an empty advisory_dispositions is refused
- **WHEN** a `completed` record carries `advisory_dispositions` as an
  empty object
- **THEN** it is refused and nothing is written

#### Scenario: a key that is not a non-empty finding id is refused
- **WHEN** an `advisory_dispositions` key is empty or not a string
- **THEN** it is refused, the refusal naming the key at fault, and
  nothing is written

#### Scenario: a finding id key that could forge a line is refused
- **WHEN** an `advisory_dispositions` key carries a character that could
  add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a disposition entry that is not an object is refused
- **WHEN** an `advisory_dispositions` value is not an object
- **THEN** it is refused, the refusal naming the finding id, and nothing
  is written

#### Scenario: a disposition entry carrying a key that is no disposition key is refused
- **WHEN** a disposition object carries a key other than `disposition`,
  `reason` or `follow_up`
- **THEN** it is refused, the refusal naming the finding id and the key
  at fault, and nothing is written

#### Scenario: a disposition outside the vocabulary is refused
- **WHEN** a disposition object's `disposition` is not one of `fixed`,
  `deferred` and `rejected`, or not a string at all
- **THEN** it is refused, the refusal naming the finding id and
  `disposition`, and nothing is written

#### Scenario: a deferred or rejected disposition without a reason is refused
- **WHEN** a `deferred` or `rejected` disposition object carries no
  `reason`
- **THEN** it is refused, the refusal naming the finding id and
  `reason`, and nothing is written

#### Scenario: a reason that is empty or not a string is refused
- **WHEN** a disposition object's `reason` is empty, all whitespace or
  not a string, on any disposition
- **THEN** it is refused, the refusal naming the finding id and
  `reason`, and nothing is written

#### Scenario: a reason that could forge a line is refused
- **WHEN** a disposition object's `reason` carries a character that
  could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a fixed disposition may carry a reason or none
- **WHEN** a `fixed` disposition object carries no `reason`, or carries
  one
- **THEN** it is admitted — `reason` is required on `deferred` and
  `rejected` alone

#### Scenario: a follow_up on a deferred disposition names a follow-up task
- **WHEN** a `deferred` disposition object carries `follow_up` naming a
  task id
- **THEN** it is admitted and reads back as given

#### Scenario: a follow_up on a fixed or rejected disposition is refused
- **WHEN** a `fixed` or `rejected` disposition object carries
  `follow_up`
- **THEN** it is refused, the refusal naming the finding id and
  `follow_up`, and nothing is written

#### Scenario: a follow_up that is not a task id is refused
- **WHEN** a `deferred` disposition object's `follow_up` is not a task
  id in the form task ids take, or not a string at all
- **THEN** it is refused, the refusal naming the finding id and
  `follow_up`, and nothing is written

#### Scenario: a follow_up that could forge a line is refused
- **WHEN** a `deferred` disposition object's `follow_up` carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The dispositions field binds a commit completion alone
A `completed` record bound by `completed_finding` carrying
`advisory_dispositions` SHALL be refused — the findings lane's
`complete --findings` takes no dispositions (ADR-0016 decision 1).

#### Scenario: advisory_dispositions on a finding-bound completion is refused
- **WHEN** a `completed` record bound by `completed_finding` carries
  `advisory_dispositions`
- **THEN** it is refused and nothing is written

### Requirement: advisory_dispositions is a field of schema 7
A `completed` record carrying `advisory_dispositions` SHALL carry schema
7: a writer carrying it SHALL stamp 7 through the minimum-schema
derivation. It SHALL NOT be admitted to a `completed` record stamped
below 7, refused at write and on read by the field-admission rule of the
record's own schema. A `completed` record without it SHALL be validated
and stamped exactly as before, and the field SHALL be declared through
the registrations the schema-7 fields use — the field family, the
family's own schema-bound rule and the minimum-schema derivation — not
by a second mechanism. Nothing reads the field yet.

#### Scenario: a completed record carrying the field stamps schema 7
- **WHEN** a `completed` record is built carrying `advisory_dispositions`
- **THEN** it carries schema 7

#### Scenario: the field on a completed record below schema 7 is refused at write
- **WHEN** a `completed` record stamped below 7 carries
  `advisory_dispositions`
- **THEN** it is refused and nothing is written

#### Scenario: the field on a completed record below schema 7 is refused on read
- **WHEN** the journal holds a `completed` record stamped below 7 that
  carries `advisory_dispositions`
- **THEN** reading the task's records refuses it

#### Scenario: a completed record without the field keeps its schema and reads as before
- **WHEN** a `completed` record carries no `advisory_dispositions`
- **THEN** it is validated and stamped exactly as before the field
  existed
