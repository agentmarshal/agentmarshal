# operator-acceptance Specification (delta)

## ADDED Requirements

### Requirement: every surface marks a self-acceptance
Where an acceptance's `accepted_by` matches a declared writer of the
candidate — an author or committer name or email, case-insensitively —
the gate's acceptance line SHALL carry
` (self-accepted: accepting party is a declared author or committer)`
and `report`'s task line a tab-separated `self-accepted` field.
`report` marks a confirmed self-acceptance only — where the commit's
writers cannot be read it prints unmarked, and `status` alone says the
check could not run (ADR-0007 decision 4).

#### Scenario: the gate's acceptance line marks a self-acceptance
- **WHEN** the acceptance over findings the gate judges carries an
  `accepted_by` matching a declared writer name or email of the
  candidate range
- **THEN** the acceptance line reads `accepted over findings <ids> by
  <party> (self-accepted: accepting party is a declared author or
  committer); not an approving review`

#### Scenario: report's task line marks a self-acceptance
- **WHEN** a task's decision derives from an acceptance whose
  `accepted_by` is a declared writer of the accepted commit
- **THEN** its report line carries a tab-separated `self-accepted`
  field after the `decision=accepted-over-findings` field

#### Scenario: an acceptance by another party prints unmarked
- **WHEN** an acceptance's `accepted_by` matches no declared writer of
  the candidate
- **THEN** the gate's acceptance line and the `report` task line print
  exactly what they print today, with no mark

#### Scenario: report's task line prints unmarked when the check cannot run
- **WHEN** the acceptance a `decision` derives from binds a commit whose
  declared writers git cannot read — or no repository answers for the
  journal at all
- **THEN** the `report` line prints as for any other acceptance —
  `decision=accepted-over-findings` and no mark; `status` alone says
  the check could not run

### Requirement: `report` derives a completed task's decision from the completed record's binding
A completed task's `decision` SHALL come from the review and the
acceptance recorded before the `completed` record and bound to its
`completed_commit`, or its `completed_finding`: `approved` on the
binding's approving latest review, else `accepted-over-findings` on a
latest `findings` acceptance bound to it (ADR-0007 decision 5). An
unbound acceptance SHALL not mark the task; a task with no `completed`
record keeps today's rule.

#### Scenario: a commit approved after an earlier commit's acceptance reports approved
- **WHEN** a task's earlier commit was accepted over findings and its
  completed commit's latest review is approved
- **THEN** its report line reads `decision=approved` and no acceptance
  mark

#### Scenario: a commit approved after its own acceptance reports approved
- **WHEN** the completed commit's latest review is approved and a
  `findings` acceptance also binds to it
- **THEN** its report line reads `decision=approved` — the binding's
  latest review decides; an acceptance covers a completion whose review
  is non-approving

#### Scenario: a commit completed over findings reports accepted-over-findings
- **WHEN** the completed commit's latest review is non-approving and an
  acceptance carrying `findings` binds to it
- **THEN** its report line reads `decision=accepted-over-findings`

#### Scenario: a finding completed over findings reports accepted-over-findings
- **WHEN** the completed finding's latest review is non-approving and an
  acceptance carrying `findings` binds to it
- **THEN** its report line reads `decision=accepted-over-findings` — the
  acceptance carries no `accepted_commit`, so no self-acceptance mark is
  derived

#### Scenario: an acceptance bound to another commit leaves no decision
- **WHEN** a task's completed commit was never approved and its only
  acceptance over findings binds to an earlier commit
- **THEN** its report line carries no `decision` field

#### Scenario: a review written after the completion does not change its decision
- **WHEN** a task's `completed` record closed over findings and a
  review bound to its `completed_commit` is recorded after a later
  `reopened`
- **THEN** its report line still reads
  `decision=accepted-over-findings` — records written after the
  `completed` record do not reach its decision

#### Scenario: a task with no completed record keeps today's decision rule
- **WHEN** a task holds an acceptance carrying `findings` and no
  `completed` record
- **THEN** its report line reads `decision=accepted-over-findings` as
  today

## MODIFIED Requirements

### Requirement: Readers keep acceptance over findings to the acceptances that carry findings
No reader SHALL treat a pause or operational acceptance as an acceptance
over findings, and none SHALL fail on an acceptance without `findings`.
The gate SHALL judge acceptance over findings by the latest acceptance of
that commit or finding that carries `findings`, on either binding — a
pause or operational acceptance written later does not shadow it. `status`
SHALL print a line for each new form naming `accepted_pause=<extension>`
or `operational` where an acceptance over findings names its findings,
with the same binding and self-acceptance marking. `report` SHALL derive
`accepted-over-findings` only from an acceptance carrying `findings`.
Every output for an acceptance carrying `findings` — the gate transcripts,
the `status` lines and the `report` line — SHALL be unchanged byte for
byte for an acceptance that is not a self-acceptance; where it is one,
the mark "every surface marks a self-acceptance" requires applies
instead. The `accept` command writes the new forms, and nothing else
SHALL act on them.

#### Scenario: a pause acceptance does not shadow an acceptance over findings
- **WHEN** an acceptance carrying `findings` stands on a commit and a pause
  or operational acceptance bound to the same commit is written later
- **THEN** the gate judges the findings acceptance and reports the accepted
  over findings line, on the commit binding as on the finding binding

#### Scenario: an acceptance without findings is not judged as one
- **WHEN** the latest acceptance bound to the candidate carries no
  `findings`
- **THEN** the gate does not report an acceptance over findings

#### Scenario: status prints a pause acceptance
- **WHEN** a task holds a pause acceptance
- **THEN** its record line names `accepted_pause=<extension>` where an
  acceptance over findings names its findings, and the summary and
  self-acceptance marking apply as for an `accepted_commit` acceptance

#### Scenario: status prints an operational acceptance
- **WHEN** a task holds an operational acceptance
- **THEN** its record line names `operational` where an acceptance over
  findings names its findings, and the summary and self-acceptance marking
  apply as for an `accepted_commit` acceptance

#### Scenario: report derives accepted-over-findings only from an acceptance carrying findings
- **WHEN** a task's acceptances carry `accepted_pause` or `operational`
  and none carries `findings`
- **THEN** its report line derives no `accepted-over-findings` decision

#### Scenario: every output for an acceptance over findings is unchanged
- **WHEN** an acceptance carries `findings` and its accepting party is no
  declared writer of the accepted commit
- **THEN** the gate transcripts, the `status` lines and the `report` line
  are byte-identical to what they were before the new forms existed
