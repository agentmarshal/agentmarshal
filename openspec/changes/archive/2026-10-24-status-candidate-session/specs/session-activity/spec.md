## ADDED Requirements

### Requirement: `status` names the session that produced the reviewed commit
`agentmarshal status <task>` SHALL print, after what it prints today,
one line for the commit the task's latest review judged — the
`reviewed_commit` the task's last `review` record carries: the
implementer session whose `commit` equals it — a session record whose
`role` is `implementer` — showing the session's id, `actor` and
`outcome`, and `report_ready` when the record carries it. When the
session's `outcome` is not `implemented` the line SHALL say the run did
not end `implemented`. When several implementer sessions name the
commit the line SHALL show the latest of them — the last in the task's
stored order — and give the count of the earlier ones.

#### Scenario: the producing implementer session is named
- **WHEN** the task's latest review carries `reviewed_commit` and an
  implementer session's `commit` equals it
- **THEN** one line names the session's id, `actor` and `outcome`,
  after the lines the view prints today

#### Scenario: report_ready prints when the record carries it
- **WHEN** the producing session's record carries `report_ready`
- **THEN** the line carries `report_ready`; a session carrying none
  shows none

#### Scenario: an outcome other than implemented is said plainly
- **WHEN** the producing session's `outcome` is not `implemented`
- **THEN** the line says the run did not end `implemented`

#### Scenario: the latest of several naming sessions is shown and the earlier counted
- **WHEN** several implementer sessions' `commit` equals the reviewed
  commit
- **THEN** the line shows the latest of them and gives the count of the
  earlier ones

### Requirement: `status` prints no session line where no implementer session names the reviewed commit
`agentmarshal status <task>` SHALL print no session line — exactly what
it prints without one — when the task's latest review binds a finding
(`reviewed_finding`), when the task holds no `review` record, and when
no session record whose `role` is `implementer` carries a `commit`
equal to the reviewed one — a candidate produced by a runner that wrote
no session is shown as before (proposal 036's disposition). A session
of another role naming the commit SHALL produce no line either.

#### Scenario: a review bound to a finding produces no line
- **WHEN** the task's latest review carries `reviewed_finding`
- **THEN** no session line prints

#### Scenario: a task holding no review produces no line
- **WHEN** the task holds no `review` record
- **THEN** no session line prints

#### Scenario: a candidate no implementer session names prints as before
- **WHEN** the task's latest review judged a commit no implementer
  session's `commit` names
- **THEN** no session line prints — the detail view is byte for byte
  what it prints without one

#### Scenario: a session of another role naming the commit produces no line
- **WHEN** a session whose `role` is not `implementer` carries a
  `commit` equal to the reviewed one
- **THEN** no session line prints

### Requirement: the session line leaves today's output unchanged and escapes record values
Every line `agentmarshal status <task>` prints today SHALL print
unchanged, the session line appended after; every value the line takes
from a record SHALL be escaped where it is displayed, as every record
value in the view is; the line SHALL refuse and block nothing.

#### Scenario: today's lines print unchanged and the session line follows
- **WHEN** `status <task>` runs for a task the line answers for
- **THEN** every line the command printed before this change prints
  unchanged, and the session line follows

#### Scenario: a record value on the session line is escaped on display
- **WHEN** a value the line takes from a record carries a character
  that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is
