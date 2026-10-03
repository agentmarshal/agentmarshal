## MODIFIED Requirements

### Requirement: The capture policy decides where a review's prose goes
Both review paths SHALL take the level for a review's prose from the capture
policy's `reviews` class, read from the project file of the journal being
written. A project file with no `capture` section SHALL resolve to the default
preset, which puts reviews at `hash`. Only `commit` SHALL put a review's prose
in the journal. At `hash` the reviewer's output SHALL be kept byte for byte in
a file under the local state's process-log area of the repository that holds
the journal, a `review-prose` event carrying the task, the file's path and its
sha256 SHALL be appended to the process log, and the journal SHALL hold
nothing about the prose — no artifact, no field. When the local state cannot
be used — git cannot name it or its directory cannot be created — the output
SHALL be kept in a local temporary file instead, and stderr SHALL say why.

#### Scenario: by default the prose stays out of the journal
- **WHEN** `agentmarshal review` records a verdict in a project whose file has
  no `capture` section
- **THEN** nothing is written under the task's artifacts directory, the record
  carries no `artifacts`, the reviewer's output is kept byte for byte in a
  file under the clone's local state, a `review-prose` event carrying the
  task, the file's path and its sha256 is appended to the process log, and
  the command names the path on stderr

#### Scenario: commit keeps today's behaviour
- **WHEN** the capture level for reviews is `commit`
- **THEN** `agentmarshal review` pins the output as a journal artifact and
  prints `reviewer prose pinned: <ref>` on stderr, as before this change

#### Scenario: off keeps nothing
- **WHEN** `agentmarshal review` records a verdict and the capture level for
  reviews is `off`
- **THEN** nothing is written under the task's artifacts directory, no
  temporary copy of the output is made, the record carries no `artifacts`, and
  stderr says the prose was not kept

#### Scenario: local state that cannot be used falls back to a temporary file
- **WHEN** `agentmarshal review` records a verdict at capture level `hash`
  and the clone's local state cannot be used — git cannot name it or its
  directory cannot be created
- **THEN** the reviewer's output is kept in a local temporary file as before
  this change, and stderr says why the local state could not be used

#### Scenario: a sidecar keeps the prose in the journal repository's local state
- **WHEN** `agentmarshal review` records a verdict at capture level `hash`
  in a sidecar placement
- **THEN** the prose file and the `review-prose` event land in the sidecar
  repository's local state, and the host's local state is untouched

#### Scenario: the human path refuses prose it may not keep
- **WHEN** `agentmarshal submit-review --prose <file>` is run and the capture
  level for reviews is not `commit`
- **THEN** the command refuses before writing anything, and its message names
  the level and the setting that permits keeping prose

#### Scenario: a malformed capture section costs no reviewer run
- **WHEN** the project file's `capture` section is malformed
- **THEN** `agentmarshal review` refuses with the parser's message before it
  launches the reviewer command, and writes nothing
