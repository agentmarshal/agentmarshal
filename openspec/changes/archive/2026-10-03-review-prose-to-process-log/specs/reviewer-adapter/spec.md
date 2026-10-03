## MODIFIED Requirements

### Requirement: The reviewer command's diagnostics survive a successful run
When the configured reviewer command exits zero, whatever it wrote to its
error stream SHALL be kept byte for byte in a file under the local state's
process-log area of the repository that holds the journal — at every capture
level — a `review-diagnostics` event carrying the file's path and its sha256
SHALL be appended to the process log, and the command SHALL say where. When
the local state cannot be used, the output SHALL be kept in a local temporary
file instead, and the command SHALL say why. A command that wrote nothing
there SHALL produce no such message.

#### Scenario: a warning from a wrapper reaches the operator
- **WHEN** the reviewer command exits zero having written to its error stream
- **THEN** the review is recorded as it is today, the output is kept under
  the clone's local state and announced by a `review-diagnostics` event, and
  the operator is told where it was kept

#### Scenario: a silent command says nothing about its silence
- **WHEN** the reviewer command exits zero having written nothing to its
  error stream
- **THEN** the output is what it is today, with no mention of a kept file

#### Scenario: diagnostics are kept at every capture level
- **WHEN** the reviewer command exits zero having written to its error stream
  and the capture level for reviews is `commit`, `hash` or `off`
- **THEN** the output is kept in a file under the clone's local state and a
  `review-diagnostics` event is appended to the process log, whatever the
  level does with the prose

#### Scenario: diagnostics fall back to a temporary file when the local state cannot be used
- **WHEN** the reviewer command exits zero having written to its error stream
  and the clone's local state cannot be used
- **THEN** the output is kept in a local temporary file as before this
  change, and the command says why the local state could not be used
