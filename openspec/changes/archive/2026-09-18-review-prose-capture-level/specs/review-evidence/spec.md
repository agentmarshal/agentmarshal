## MODIFIED Requirements

### Requirement: A review may carry the reviewer's prose as a pinned artifact
A review record MAY carry `artifacts`: a list of `{ref, hash}` where `ref` is
a path relative to the project root under
`.agentmarshal/journal/tasks/<task>/artifacts/` and `hash` is the sha256 of
that file's bytes. When a review path keeps prose in the journal, it SHALL keep
the reviewer's output as received, unedited, and SHALL write the file before
the record that pins it. Once the prose is pinned, the review path SHALL keep
no other copy of it outside the journal.

#### Scenario: the model review path keeps its output
- **WHEN** `agentmarshal review` receives reviewer output that yields a valid
  verdict, and the capture level for reviews is `commit`
- **THEN** the launcher writes that output to
  `.agentmarshal/journal/tasks/<task>/artifacts/<review-record-id>-review.md`
  and the review record it writes carries one artifact pinning that file

#### Scenario: an accepted verdict keeps no copy outside the journal
- **WHEN** `agentmarshal review` has pinned the reviewer's output
- **THEN** it writes no copy of that output anywhere else, and tells the
  operator the artifact's path and nothing about a temporary file

#### Scenario: the human review path attaches prose
- **WHEN** `agentmarshal submit-review` is given `--prose <file>` and the
  capture level for reviews is `commit`
- **THEN** the file's bytes are copied to the same location and pinned on the
  record; without `--prose` the record carries no `artifacts`, as before

#### Scenario: a rejected verdict still keeps the prose
- **WHEN** reviewer output fails verdict validation
- **THEN** the output is kept where the operator can read it, as before, at
  every capture level, and no review record is written

## ADDED Requirements

### Requirement: The capture policy decides where a review's prose goes
Both review paths SHALL take the level for a review's prose from the capture
policy's `reviews` class, read from the project file of the journal being
written. A project file with no `capture` section SHALL resolve to the default
preset, which puts reviews at `hash`. Only `commit` SHALL put a review's prose
in the journal.

#### Scenario: by default the prose stays out of the journal
- **WHEN** `agentmarshal review` records a verdict in a project whose file has
  no `capture` section
- **THEN** nothing is written under the task's artifacts directory, the record
  carries no `artifacts`, and the reviewer's output is kept in a local
  temporary file whose path the command names on stderr

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

#### Scenario: the human path refuses prose it may not keep
- **WHEN** `agentmarshal submit-review --prose <file>` is run and the capture
  level for reviews is not `commit`
- **THEN** the command refuses before writing anything, and its message names
  the level and the setting that permits keeping prose

#### Scenario: a malformed capture section costs no reviewer run
- **WHEN** the project file's `capture` section is malformed
- **THEN** `agentmarshal review` refuses with the parser's message before it
  launches the reviewer command, and writes nothing
