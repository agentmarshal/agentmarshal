# gate-lanes Specification

## Purpose
Which of the gate's checks a caller is in a position to ask for, and how the
transcript reports the ones it was not. A caller that cannot yet have a review —
a provider's CI, running on a head no review can name — gets everything else,
and reads what was left unexamined rather than inferring it from silence.

## Requirements

### Requirement: The gate can be asked to judge what does not depend on a review
The gate SHALL accept a request to evaluate the checks that do not depend on a
review record. In that mode, when the candidate has no review record at all, the
review-bound checks SHALL be reported as not examined, with the reason, and
SHALL NOT refuse the candidate. Every other check SHALL be evaluated as it is
without the mode.

#### Scenario: a candidate with no review passes the checks that do not need one
- **WHEN** the gate is asked to judge without a review and the candidate has no
  review record for its commit
- **THEN** the transcript reports the review-bound checks as not examined,
  naming the absence as the reason, and the gate's verdict rests on the
  remaining checks

#### Scenario: the mode does not excuse a candidate that breaks another rule
- **WHEN** the gate is asked to judge without a review and the candidate changes
  a path outside its contract's scope
- **THEN** the gate refuses, exactly as it does without the mode

### Requirement: The mode never weakens a candidate that has been reviewed
When a review record exists for the candidate, the review-bound checks SHALL be
evaluated whether or not the mode was requested, and their outcome SHALL be what
it is without it.

#### Scenario: a non-approving review still refuses
- **WHEN** the gate is asked to judge without a review and the candidate's
  latest review is non-approving
- **THEN** the gate refuses, and its transcript reports the review check as it
  does without the mode

#### Scenario: an approving review is reported as approving
- **WHEN** the gate is asked to judge without a review and the candidate's
  latest review is approving
- **THEN** the review-bound checks report their usual result and nothing says
  they were skipped

### Requirement: A default run is unchanged
A gate run that does not request the mode SHALL produce the transcript it
produces today, byte for byte, in every placement and on every lane — the
transcript pinned by fixtures committed in the repository, one for each
case the pin covers. A run's stdout, stderr and exit status
SHALL each equal the fixture for its lane and placement, compared after one
substitution replaces the values that differ from run to run — commit
hashes, temporary paths, record ids, times — with named placeholders, so
the comparison is exact everywhere else. Any change to a fixture SHALL be
made, and named, by the task that changes the output: the fixture is
regenerated only when the test is explicitly asked to, and the fixture's
diff is part of that task's reviewed change.

#### Scenario: the pinned transcript still matches
- **WHEN** the gate runs without the mode on a candidate the pinned
  transcript fixtures cover — the implementation lane and the journal-only
  lane in the embedded placement; in the sidecar placement the
  implementation lane and the host candidate whose diff touches only the
  journal, whose fixture pins the refusal because the deterministic lane
  does not exist there (ADR-0008 decision 2)
- **THEN** its stdout, its stderr and its exit status equal the committed
  fixture once run-dependent values are replaced by named placeholders

#### Scenario: a transcript difference is shown, not hidden
- **WHEN** a gate run's transcript differs from the committed fixture for
  its lane and placement
- **THEN** the pinned test fails and shows the difference as a readable
  diff between fixture and run

#### Scenario: a fixture changes only when the output changes on purpose
- **WHEN** a task changes the gate's default output on purpose
- **THEN** that task regenerates the fixtures — which the test rewrites
  only when explicitly asked — and the change to each fixture is part of
  the task's reviewed change, naming the output change it makes

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
