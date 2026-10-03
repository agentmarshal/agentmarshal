## ADDED Requirements

### Requirement: The transcript reports the task's changes_required count
On the implementation lane — in the embedded placement and in a sidecar —
a gate run that evaluates a candidate SHALL print one line carrying the
task's count of `changes_required` review verdicts over the whole task —
every review record of the task, whatever commit it names — and the
project's `review.changes_required_threshold` (default 3), read through
the project settings. When the count has reached the threshold the line
SHALL be marked, the signal to stop and revisit the contract. The line
reports; it decides nothing: it SHALL NOT add a violation, change the
run's exit status, or refuse a merge. A threshold setting that cannot be
read SHALL be named on the line and SHALL NOT fail the run.

#### Scenario: the implementation lane prints the count
- **WHEN** the gate evaluates a candidate on the implementation lane
- **THEN** the transcript carries one line naming the task's count of
  `changes_required` verdicts over every review record of the task and
  the project's threshold

#### Scenario: the count is over the whole task
- **WHEN** the task's earlier commits drew `changes_required` verdicts
  and the candidate's own latest review approves
- **THEN** the line's count covers every review record of the task, not
  only the records naming the candidate's commit

#### Scenario: a count at the threshold is marked
- **WHEN** the task's count of `changes_required` verdicts has reached
  the project's threshold
- **THEN** the count line is marked as reaching it, and the run's verdict
  and exit status are what they would be without the line

#### Scenario: a malformed threshold is reported on the line
- **WHEN** `review.changes_required_threshold` cannot be read as a valid
  threshold
- **THEN** the count line names the unreadable threshold, the count still
  prints, and the run is otherwise what it was

#### Scenario: the journal-only lane prints no count line
- **WHEN** a gate run takes the journal-only lane
- **THEN** its transcript carries no `changes_required` count line
