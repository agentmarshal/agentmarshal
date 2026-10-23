## ADDED Requirements

### Requirement: `brief` names the task's last failing check
`agentmarshal brief --task <id>` SHALL carry one section naming the
task's most recent `check` record whose `result` is `failed` or `error`
— most recent by the journal's record order, the record-id (ULID) order
the rest of the brief reads records in. The section SHALL give the
check's `name`, its `result`, its `commit` in the short form, and
`failed_step` and `run_url` when the record carries them, and the
`excerpt` when it carries one; and it SHALL say in one sentence that a
check record is the observer's declaration, not proof (ADR-0017
decision 2). Every value the section takes from the record SHALL be
escaped on display as the rest of the brief escapes record values.

#### Scenario: the brief names the last failing check
- **WHEN** `agentmarshal brief --task` renders a task whose most recent
  `check` record with result `failed` carries `failed_step`, `excerpt`
  and `run_url`
- **THEN** one section names the check's name, its result, the commit's
  short form, the failed step, the run link and the excerpt

#### Scenario: an error result is a failing check
- **WHEN** the task's most recent failing `check` record carries
  `result: error`
- **THEN** the section names it the same way

#### Scenario: the most recent failing record is the one named
- **WHEN** a task carries more than one `check` record with a failing
  result
- **THEN** the section names the last one in record order

#### Scenario: the optional fields are absent
- **WHEN** the last failing `check` record carries none of
  `failed_step`, `excerpt` and `run_url`
- **THEN** the section shows the name, the result and the short commit,
  and nothing of the fields the record does not carry

#### Scenario: the section says the record is a declaration
- **WHEN** the brief renders the failing-check section
- **THEN** it states in one sentence that a check record is the
  observer's declaration, not proof

#### Scenario: a check record's values stay on their own lines
- **WHEN** `agentmarshal brief --task` renders a `check` record whose
  `name`, `result`, `failed_step`, `excerpt` or `run_url` carries a
  character that could add a line to rendered output or reorder it — a
  value an older schema's journal can hold where today's read rules do
  not reach
- **THEN** each refused character prints as its escape

### Requirement: A failure the same check later passed on a later commit is named
When the journal holds, after the failing record in record order, a
`check` record of the same `name` whose `result` is `passed` and whose
`commit` differs, the section SHALL say so, naming that record's
`commit` in its short form — so a fix round is not sent after a failure
already fixed. A pass bound to the same commit or recorded under another
name SHALL NOT be named.

#### Scenario: a later pass on a later commit is named
- **WHEN** a `check` record of the same name and a different commit,
  carrying `result: passed`, follows the last failing record in record
  order
- **THEN** the section names that record's commit in its short form

#### Scenario: a pass on the same commit is not a fix
- **WHEN** the only later `passed` record of the same name is bound to
  the same commit
- **THEN** the section names no later pass

#### Scenario: a pass under another name is not a fix
- **WHEN** every later `passed` record carries a different `name`
- **THEN** the section names no later pass

#### Scenario: a pass recorded before the failure is not a fix
- **WHEN** a `passed` record of the same name precedes the last failing
  record in record order
- **THEN** the section names no later pass

#### Scenario: the latest later pass is the one named
- **WHEN** more than one later `passed` record of the same name names a
  different commit
- **THEN** the section names the most recent one's commit in its short
  form

### Requirement: A task with no failing check is briefed exactly as before
A task carrying no `check` record whose `result` is `failed` or `error`
SHALL yield the brief it yielded before this change — byte for byte, no
section and no other difference.

#### Scenario: no check records means no section
- **WHEN** a task carries no `check` record
- **THEN** the brief is byte for byte what it was before this change

#### Scenario: only passing and skipped checks mean no section
- **WHEN** every `check` record the task carries has `result` `passed`
  or `skipped`
- **THEN** the brief is byte for byte what it was before this change
