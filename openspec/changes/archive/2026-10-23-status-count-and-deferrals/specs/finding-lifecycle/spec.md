## MODIFIED Requirements

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
command's `--disposition` supplies it; the `status` view shows the open
deferrals it records.

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

## ADDED Requirements

### Requirement: `status` prints the task's count of `changes_required` verdicts
`agentmarshal status <task>` SHALL print one line carrying the task's
count of `changes_required` review verdicts when the count is at least
one — counted over every review record of the task's candidates exactly
as the gate's line counts them since CR-168: whatever commit a review
names, and a review bound to a research finding (`reviewed_finding`,
ADR-0009) is not counted. The line SHALL name the project's
`review.changes_required_threshold` (default 3) read through the project
settings, SHALL be marked when the count has reached the threshold — the
signal to stop and revisit the contract (ADR-0016 decision 4) — and
SHALL name the threshold when it cannot be read. The line reports; it
SHALL NOT block anything. A task with no `changes_required` verdict
SHALL get no count line.

#### Scenario: the count line prints when at least one verdict is changes_required
- **WHEN** the task's reviews carry at least one `changes_required`
  verdict over its candidates
- **THEN** `status <task>` prints one line `changes_required verdicts
  for <task>: N (threshold T)` naming the count and the project's
  threshold

#### Scenario: the count covers every review of the task's candidates
- **WHEN** the task's reviews of different commits drew
  `changes_required` verdicts
- **THEN** the count covers every such review, not only reviews of one
  commit

#### Scenario: a review bound to a research finding is not counted
- **WHEN** the task carries a `changes_required` review bound to a
  research finding alongside reviews of its candidates
- **THEN** the count covers only the reviews of the task's candidates

#### Scenario: a count at the threshold is marked
- **WHEN** the task's count of `changes_required` verdicts has reached
  the project's threshold
- **THEN** the line is marked as reaching it — `threshold T reached —
  stop and revisit the contract` — and nothing else about the view
  changes

#### Scenario: a malformed threshold is named on the line
- **WHEN** `review.changes_required_threshold` cannot be read as a
  valid threshold
- **THEN** the count still prints and the line names the unreadable
  threshold

#### Scenario: no count line when the count is zero
- **WHEN** the task carries no `changes_required` review over its
  candidates
- **THEN** `status <task>` prints no count line

### Requirement: `status` lists the open deferrals of the task's completion
For a task whose `completed` record carries `advisory_dispositions`,
`agentmarshal status <task>` SHALL print a `Deferrals` section listing
each `deferred` finding on a line of its own with its `reason` and, when
present, its `follow_up` task — and that task's state when the journal
holds it (`load_task_status`), or that the journal does not hold it, an
ordinary answer rather than an error. `fixed` and `rejected` entries
SHALL be counted on one `fixed=N rejected=M` line, not listed. A task
whose completions carry no `advisory_dispositions` SHALL get no
`Deferrals` section (ADR-0016 decision 1).

#### Scenario: each deferred finding is listed with its reason
- **WHEN** the `completed` record's `advisory_dispositions` carries
  `deferred` entries
- **THEN** the `Deferrals` section lists each on a line naming the
  finding id and its reason

#### Scenario: a follow-up task held by the journal shows its state
- **WHEN** a `deferred` entry carries `follow_up` naming a task the
  journal holds
- **THEN** the line names the task and its state

#### Scenario: a follow-up task the journal does not hold is named
- **WHEN** a `deferred` entry carries `follow_up` naming a task the
  journal does not hold
- **THEN** the line names the task and says the journal does not hold
  it — not an error

#### Scenario: fixed and rejected dispositions are counted on one line
- **WHEN** the `completed` record's `advisory_dispositions` carries
  `fixed` and `rejected` entries
- **THEN** they are counted on one `fixed=N rejected=M` line, not
  listed

### Requirement: a task without the marks keeps today's detail view byte for byte
A task with no `changes_required` verdict over its candidates and no
`advisory_dispositions` on its `completed` records SHALL print exactly
the detail view `status` printed before the lines existed. Every value
the new lines take from a record SHALL be escaped on display — a
refused character can neither add a line nor reorder one (ADR-0015
decision 5).

#### Scenario: the detail view is byte for byte unchanged without the marks
- **WHEN** the task has no `changes_required` verdict and no
  `advisory_dispositions`
- **THEN** `status <task>` prints exactly the detail view it printed
  before the lines existed

#### Scenario: every value from a record is escaped on display
- **WHEN** a disposition reason or finding id carries a character the
  forgeable-text rule refuses
- **THEN** it prints escaped on the deferral line
