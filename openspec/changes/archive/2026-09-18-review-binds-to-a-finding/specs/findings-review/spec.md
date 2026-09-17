## Purpose
What a review of a finding is run against, what the reviewer is given, and when
the launcher refuses instead of reviewing. A finding pins its artifacts by
hash; a review of it must judge those bytes, not whatever the working tree
holds when the review is read.

## ADDED Requirements

### Requirement: A review can be launched against a finding
The review launcher SHALL accept the latest finding of the same task in place of
a commit, and the review it records SHALL name that finding and no commit. The
verdict the reviewer prints SHALL name the finding it judged, and a verdict
naming a different finding — or a commit — SHALL be refused without a record.

#### Scenario: the reviewer judges a finding and the record binds to it
- **WHEN** a review is launched against a finding of the task
- **THEN** the recorded review names that finding, names no commit, and carries
  the reviewer's prose the way a review of a commit does

#### Scenario: a verdict about another subject is refused
- **WHEN** the reviewer's verdict names a finding other than the one asked
  about, or names a commit
- **THEN** no review is recorded and the refusal says what was asked and what
  the verdict named

### Requirement: The reviewer is given the pinned bytes, and drift refuses the launch
Before running the reviewer the launcher SHALL verify every artifact reference
that resolves to a file under the project root against the hash the finding
recorded, and SHALL refuse the launch when any of them differs. The content the
reviewer is given SHALL be read from those verified paths. A finding none of
whose references resolve under the project root SHALL be refused: there would be
nothing verifiable to review.

#### Scenario: an edited artifact refuses the review
- **WHEN** an artifact the finding pins no longer hashes to the recorded value
- **THEN** no reviewer is run, no review is recorded, and the refusal names the
  artifact

#### Scenario: a finding with nothing verifiable is refused
- **WHEN** none of the finding's references resolve to a file under the project
  root
- **THEN** no reviewer is run and the refusal says that nothing could be
  verified

#### Scenario: a reference that does not resolve is named, not verified
- **WHEN** a finding pins several references and only some resolve under the
  project root
- **THEN** the reviewer is given the verified ones, and the prompt names each
  reference that could not be verified

### Requirement: The launcher refuses before it spends a reviewer run
The launcher SHALL refuse, without running the reviewer, a finding that is not
the task's latest and a reviewer whose declared identity is not independent of
the finding's recorder. Both are conditions the findings lane refuses after the
fact, and a review recorded under either cannot be withdrawn from an
append-only journal.

#### Scenario: a finding that is not the latest is refused
- **WHEN** a review is launched against a finding of the task that a later
  finding supersedes
- **THEN** no reviewer is run, no review is recorded, and the refusal names the
  latest finding

#### Scenario: a reviewer who is not independent of the recorder is refused
- **WHEN** the declared reviewer identity is one of the finding recorder's
  declared git identities, or the recorder resolves to no git identity at all
- **THEN** no reviewer is run, no review is recorded, and the refusal gives the
  reason the findings lane would give

### Requirement: Artifact content cannot introduce a verdict
Artifact content the prompt carries SHALL be presented so that no line of it
can be read as the verdict protocol's own output: the protocol's sentinels
occur in the prompt only where the launcher put them. The prompt SHALL say how
the content is presented, so a reviewer does not report the presentation as
part of the content.

#### Scenario: an artifact carrying the verdict sentinels yields no verdict of its own
- **WHEN** a pinned artifact's content contains the verdict sentinels and a
  complete verdict block at the start of a line
- **THEN** the built prompt contains no sentinel line outside the protocol's
  own instruction, and the embedded copy cannot be parsed as a verdict

### Requirement: The commit path is unchanged
The prompt, the snapshot and the recorded fields of a review launched against a
commit SHALL be unchanged by the existence of the finding path.

#### Scenario: the pinned commit prompt still matches byte for byte
- **WHEN** a review is launched against a commit
- **THEN** the prompt the reviewer receives is byte-for-byte what it was before
  this change
