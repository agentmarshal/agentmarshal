## ADDED Requirements

### Requirement: The material that carries a contract carries its amendment history
The review prompt and the implementer's brief SHALL render the task's amendment
records after the contract they already carry. Each entry SHALL state the time
the amendment was recorded and its reason, and SHALL name the recorder when the
record carries one. The rendering SHALL be built from the records; nothing in
this capability SHALL parse the contract document for history.

#### Scenario: a reviewer is told that a criterion is younger than the task
- **WHEN** `agentmarshal review` builds a prompt for a task whose journal holds
  amendment records
- **THEN** the prompt carries one entry per amendment record, each with its time
  and its reason, after the contract text

#### Scenario: an implementer is told the same
- **WHEN** `agentmarshal brief --task` renders a task whose journal holds
  amendment records
- **THEN** the brief carries the same entries, in the order the records were
  written

#### Scenario: an amendment recorded without an actor still renders
- **WHEN** an amendment record carries no recorder
- **THEN** its entry renders with its time and reason and says nothing about who
  recorded it

#### Scenario: a task with no amendments is unchanged
- **WHEN** a task's journal holds no amendment record
- **THEN** the prompt and the brief are byte for byte what they were before this
  change, and the pinned prompt test passes unmodified

### Requirement: The history is read from the journal the command works in
The rendering SHALL read amendment records from the journal the command is
operating on — the working tree in an embedded journal, the sidecar's journal in
a sidecar — and not from the reviewed commit's snapshot.

#### Scenario: an amendment recorded after the candidate was built is rendered
- **WHEN** an amendment is recorded after the commit under review was created
- **THEN** the review prompt for that commit carries the amendment, although the
  contract text in the same prompt predates it
