## ADDED Requirements

### Requirement: The reviewer command's diagnostics survive a successful run
When the configured reviewer command exits zero, whatever it wrote to its error
stream SHALL be kept where the operator can read it, and the command SHALL say
where. A command that wrote nothing there SHALL produce no such message.

#### Scenario: a warning from a wrapper reaches the operator
- **WHEN** the reviewer command exits zero having written to its error stream
- **THEN** the review is recorded as it is today, and the operator is told
  where that output was kept

#### Scenario: a silent command says nothing about its silence
- **WHEN** the reviewer command exits zero having written nothing to its error
  stream
- **THEN** the output is what it is today, with no mention of a kept file
