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
A `completed` record carrying `advisory_dispositions` SHALL carry
schema 7: a writer carrying it SHALL stamp 7 through the
minimum-schema derivation. It SHALL NOT be admitted to a `completed`
record stamped below 7, refused at write and on read by the
field-admission rule of the record's own schema. A `completed` record
without it SHALL be validated and stamped exactly as before, and the
field SHALL be declared through the registrations the schema-7 fields
use — the field family, the family's own schema-bound rule and the
minimum-schema derivation — not by a second mechanism. The `complete`
command's `--disposition` supplies it; the views of open deferrals are
later work.

#### Scenario: a completed record carrying the field stamps schema 7
- **WHEN** a `completed` record is built carrying
  `advisory_dispositions`
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

### Requirement: `complete` takes a disposition for each advisory finding of the review the gate passed on
`agentmarshal complete` SHALL take a repeatable `--disposition
<finding id>=<disposition>` — `<disposition>` one of `fixed`,
`deferred:<reason>` and `rejected:<reason>`, the reason everything
after the first colon, so it may contain colons — and a repeatable
`--follow-up <finding id>=<task>` naming a follow-up task for a
`deferred` finding. For the review the gate passed on — the latest
review of the resolved commit, the approving one or the non-approving
one an acceptance covered, the same one the gate's verdict check
consults — the command SHALL write the answers into the `completed`
record's `advisory_dispositions` through `create_completed_record`'s
parameter: each reason landing as `reason`, each `--follow-up` landing
as `follow_up` on its finding's entry. When the review carries no
advisory findings the command SHALL complete exactly as before: no
flag needed, no field written.

#### Scenario: a completion answers each advisory finding of the approving review
- **WHEN** the approving latest review of the candidate carries
  advisory findings and `complete` is given a `--disposition` for each
- **THEN** the `completed` record's `advisory_dispositions` carries
  each finding's entry and the record is written

#### Scenario: a deferred disposition may name a follow-up task
- **WHEN** `complete` is given `--disposition F-1=deferred:<reason>`
  and `--follow-up F-1=<task>` for a deferred advisory finding
- **THEN** the finding's entry carries `follow_up` with that task

#### Scenario: a reason is everything after the first colon
- **WHEN** a `--disposition` reason itself contains colons
- **THEN** the recorded `reason` is everything after the value's first
  colon

#### Scenario: a fixed disposition may carry a reason
- **WHEN** `complete` is given `--disposition F-1=fixed:<reason>`
- **THEN** the finding's entry carries the reason, as the field admits
  a `reason` on `fixed`

#### Scenario: the review the gate passed on may be a non-approving review an acceptance covered
- **WHEN** the latest review of the candidate does not approve, an
  acceptance covers its blocking findings, and the review carries
  advisory findings
- **THEN** `complete` takes a disposition for each of that review's
  advisory findings, written into the `completed` record

#### Scenario: a review with no advisory findings completes as before
- **WHEN** the review the gate passed on carries no advisory findings
- **THEN** `complete` with no flags writes the `completed` record
  exactly as before, carrying no `advisory_dispositions`

### Requirement: `complete` refuses before writing when a disposition is missing, unknown or refused
After the gate passes and before `completed` is written, `complete`
SHALL refuse — writing nothing — when:

- any advisory finding of the review the gate passed on has no
  `--disposition`, the refusal naming every unanswered finding id;
- a `--disposition` or `--follow-up` names an id that is not an
  advisory finding of that review, the refusal naming the id;
- a `deferred` or `rejected` is given with no reason;
- a `--follow-up` lands on a disposition other than `deferred`;
- a flag value fails the record's own rules, the refusal repeated
  naming the flag it came through; or
- a flag is malformed — no `=`, an empty id, an empty follow-up task —
  or an id is given twice.

#### Scenario: an unanswered advisory finding refuses, naming every unanswered id
- **WHEN** any advisory finding of the review the gate passed on has
  no `--disposition`
- **THEN** `complete` refuses before writing `completed`, naming every
  unanswered id, and no `completed` record exists

#### Scenario: a disposition for an id the review did not raise refuses, naming the id
- **WHEN** a `--disposition` names an id that is not an advisory
  finding of the review the gate passed on
- **THEN** `complete` refuses naming the id and writes nothing

#### Scenario: a follow-up for an id the review did not raise refuses, naming the id
- **WHEN** a `--follow-up` names an id that is not an advisory finding
  of the review the gate passed on
- **THEN** `complete` refuses naming the id and writes nothing

#### Scenario: a deferred or rejected without a reason refuses
- **WHEN** `complete` is given `deferred` or `rejected` with no reason
- **THEN** it refuses naming the id and the flag, and writes nothing

#### Scenario: a follow-up on a disposition other than deferred refuses
- **WHEN** a `--follow-up` lands on a `fixed` or `rejected` entry
- **THEN** `complete` refuses naming the id and `--follow-up`, and
  writes nothing

#### Scenario: a value the record rules refuse is refused naming the flag
- **WHEN** a flag value fails the record's own rules — a disposition
  word outside the vocabulary, a string that could forge a line, or a
  `follow_up` that is not a task id
- **THEN** `complete` refuses naming the flag it came through and
  writes nothing

#### Scenario: a malformed flag refuses
- **WHEN** a `--disposition` or `--follow-up` carries no `=`, an empty
  id, or an empty follow-up task
- **THEN** `complete` refuses naming the flag and writes nothing

#### Scenario: a flag repeated for one id refuses
- **WHEN** `--disposition` or `--follow-up` is given twice for one id
- **THEN** `complete` refuses naming the id and writes nothing

### Requirement: the findings lane takes no dispositions
`complete --findings` SHALL take no dispositions: a `--disposition` or
`--follow-up` there SHALL be refused, and the lane SHALL gain no
refusal for want of a disposition — a findings-lane completion runs
exactly as before (ADR-0016 decision 1).

#### Scenario: the disposition flags are refused on the findings lane
- **WHEN** `complete --findings` is given a `--disposition` or
  `--follow-up`
- **THEN** it refuses and writes nothing

#### Scenario: a findings completion without flags is unchanged
- **WHEN** `complete --findings` runs with no disposition flags
- **THEN** it completes exactly as before, the `completed` record
  binding `completed_finding`
