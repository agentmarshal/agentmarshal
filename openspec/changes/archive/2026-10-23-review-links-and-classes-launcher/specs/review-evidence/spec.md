## ADDED Requirements

### Requirement: A launched review links the task's previous review

`agentmarshal review` — in its commit form and its finding-review form —
SHALL write `previous_review` on the review record it writes: the id of
the task's latest review record at launch time — the latest the task's
records hold when the launch begins, read before the reviewer command
runs so a concurrent write cannot make a review link to itself — whatever
that review bound to. A task carrying no earlier review record SHALL
yield a record with no `previous_review` field. `submit-review` SHALL NOT
write the field.

#### Scenario: a second launched review links the first
- **WHEN** `agentmarshal review` records a verdict on a task that already
  carries a review record
- **THEN** the record's `previous_review` is the earlier review's id —
  whatever it bound to — and the record stamps schema 7

#### Scenario: the first launched review carries no link
- **WHEN** `agentmarshal review` records a verdict on a task carrying no
  review record
- **THEN** the record carries no `previous_review` field

#### Scenario: a launched finding review links the same way
- **WHEN** `review --reviewed-finding` records a verdict on a task that
  already carries a review record
- **THEN** the record's `previous_review` is the earlier review's id

#### Scenario: the link names the latest review at launch time
- **WHEN** `review` launches on a task carrying a review and another
  review record is written while the reviewer runs
- **THEN** the launched record's `previous_review` is the review the
  task carried when the launch began — never the concurrent one, and
  never the launched record's own id

#### Scenario: submit-review writes no link
- **WHEN** `submit-review` records a verdict on a task that already
  carries a review record
- **THEN** the record carries no `previous_review` field

### Requirement: The verdict may carry a class per finding id and the prompt says so

The verdict protocol SHALL admit an optional `classes` object mapping
finding ids to class strings — one class per finding id reported,
blocking or advisory. The prompt the launcher builds, for either binding,
SHALL list the project's finding-class vocabulary —
`review.finding_classes`, the default when unset — and ask for one class
per finding id.

#### Scenario: the prompt lists the default vocabulary
- **WHEN** the launcher builds the review prompt for a project that does
  not set `review.finding_classes`
- **THEN** the prompt names each default class and asks for one class per
  finding id reported

#### Scenario: the prompt lists the project's configured vocabulary
- **WHEN** `review.finding_classes` is set in the journal repository's
  project file
- **THEN** the prompt lists that vocabulary instead

#### Scenario: a classes object is admitted by the protocol
- **WHEN** a verdict carries `classes` mapping finding ids to class
  strings
- **THEN** the verdict parses — `classes` is an optional key, never an
  unknown one

### Requirement: The launcher records the classes a verdict names, dropping what it cannot keep

When a launched review's verdict carries `classes`, the record SHALL
carry a `classes` entry for each id among the verdict's `findings` and
`advisory_findings`: the class given when it is in the project's
vocabulary, `other` when it is not — with a warning naming the id and
the class given. An entry for an id the verdict does not carry SHALL be
dropped with a warning, and a `classes` that is not an object — or holds
a value that is not a usable class string — SHALL be dropped as a whole
with a warning. A verdict SHALL NOT be refused over a class: the run is
paid and the class is reference markup. A verdict carrying no `classes`
SHALL be recorded exactly as before — no `classes` field.

#### Scenario: classes for the verdict's ids are recorded
- **WHEN** a verdict carries `classes` naming classes of the vocabulary
  for ids among its `findings` and `advisory_findings`
- **THEN** the record carries them, and the review stamps schema 7

#### Scenario: a class outside the vocabulary records as other with a warning
- **WHEN** a verdict's `classes` names, for a finding id it carries, a
  class the vocabulary does not know
- **THEN** the record carries `other` for the id and the command prints a
  warning naming the id and the class given

#### Scenario: an entry for an id the verdict does not carry is dropped with a warning
- **WHEN** a verdict's `classes` names an id that is not among its
  `findings` or `advisory_findings`
- **THEN** that entry is dropped with a warning and the entries for the
  verdict's ids are recorded

#### Scenario: a classes that is not an object is dropped whole with a warning
- **WHEN** a verdict's `classes` is not an object
- **THEN** the verdict is recorded, no `classes` field lands and a
  warning says the value was dropped

#### Scenario: a classes holding a value that is no class string is dropped whole
- **WHEN** a verdict's `classes` holds a value that is not a non-empty
  string
- **THEN** the whole object is dropped with a warning — the verdict is
  never refused over a class — and the record carries no `classes`

#### Scenario: a verdict without classes records exactly as before
- **WHEN** a verdict carries no `classes`
- **THEN** the record carries no `classes` field — and its schema stamp
  rises only where `previous_review` asks it

## MODIFIED Requirements

### Requirement: Without --actor the review paths are unchanged

Without `--actor` both paths SHALL write the same record, stamp the same
schema and print the same lines as before the flag existed — apart from
the `previous_review` link and the `classes` a launched review records of
its own, which are the launcher's and not the flag's: the flag adds a
capability, never an obligation.

#### Scenario: a review written without --actor is byte-for-byte as before
- **WHEN** `submit-review` or `review` records a verdict without
  `--actor`
- **THEN** the record — apart from its id and times — is byte-for-byte
  the record the command wrote before the flag existed, less the
  `previous_review` and `classes` a launched review records regardless of
  the flag, and every line the command prints is unchanged
