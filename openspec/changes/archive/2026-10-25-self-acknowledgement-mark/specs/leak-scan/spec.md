# leak-scan Specification (delta)

## ADDED Requirements

### Requirement: the acknowledgement mark identifies a self-acknowledgement
Where an acknowledgement's acknowledging party is a declared author or
committer of the commit `leak-scan` scans — of any commit in the
candidate range for the gate — the mark SHALL say `self-acknowledged`,
the term `status` uses. Any other acknowledgement, and a check git
cannot answer, SHALL print exactly as today (ADR-0021 decision 5).

#### Scenario: the standalone command marks a self-acknowledgement
- **WHEN** an acknowledgement bound to the scanned commit records a
  party that is a declared author or committer of that commit
- **THEN** the hit's mark reads `self-acknowledged by <recorded_by>:
  <reason>`

#### Scenario: the gate marks a self-acknowledgement over the candidate range
- **WHEN** an acknowledgement bound to the candidate records a party
  that is a declared writer of a commit in the candidate range
- **THEN** the gate's advisory line marks the hit `self-acknowledged`

#### Scenario: the commit's committer marks a self-acknowledgement
- **WHEN** the acknowledging party matches the scanned commit's
  declared committer and not its author
- **THEN** the mark says `self-acknowledged`

#### Scenario: a declared actor's resolved identity marks a self-acknowledgement
- **WHEN** the acknowledging party is a declared actor whose git
  identities include a declared writer of the scanned commit
- **THEN** the mark says `self-acknowledged` — the actor's resolved
  identities are compared, not only the recorded name

#### Scenario: a writer of an earlier range commit marks at the gate alone
- **WHEN** the acknowledging party is a declared writer of an earlier
  commit of the candidate range but not of the candidate the record
  binds
- **THEN** the gate's line says `self-acknowledged` and the standalone
  command's mark on that commit does not — it compares against the
  scanned commit's writers alone

#### Scenario: an acknowledgement by another party prints unmarked
- **WHEN** the acknowledging party is no declared writer
- **THEN** both surfaces print the mark exactly as today —
  `acknowledged by`, never `self-acknowledged`

#### Scenario: a check git cannot answer marks nothing
- **WHEN** the writer lookup cannot answer for the commit or the range
- **THEN** the mark prints as for any other acknowledgement — only a
  confirmed self-acknowledgement is marked, and `status` alone says the
  check did not run

#### Scenario: the writer check folds case
- **WHEN** the acknowledging party matches a declared writer only
  under case folding
- **THEN** the mark says `self-acknowledged`
