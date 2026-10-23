## ADDED Requirements

### Requirement: report --findings lists the finding classes recorded on reviews
`agentmarshal report --findings` SHALL print, instead of the economics
report, the finding classes the reviews of the tasks in scope record:
one `Classes` line per class — `Classes	<class>	count=<n>
examples=<id>,<id>,<id>` — ordered by class name, the count covering
every `classes` entry the in-scope review records carry, and the
examples naming up to three distinct finding ids of the class in the
order the records give them (ADR-0016 decision 3). With `--task` the
view SHALL scope to the one task's reviews. A scope recording no class
SHALL print `Classes	(none)`.

#### Scenario: each class prints with its count and up to three example finding ids
- **WHEN** `report --findings` runs over reviews carrying `classes`
- **THEN** one `Classes` line prints per class, ordered by class name,
  carrying the count of the class's entries and up to three example
  finding ids

#### Scenario: more than three findings of a class give three examples
- **WHEN** a class's entries number more than three
- **THEN** its `Classes` line names three example finding ids

#### Scenario: classes are counted across tasks
- **WHEN** reviews of two tasks record the same class
- **THEN** the class's count covers the entries of both tasks' reviews

#### Scenario: --task scopes the classes view to the one task
- **WHEN** `report --findings --task <id>` runs
- **THEN** the `Classes` lines cover only that task's reviews

#### Scenario: with no classes recorded the view says so
- **WHEN** `report --findings` runs and no in-scope review carries
  `classes`
- **THEN** the classes section prints `Classes	(none)`

### Requirement: report --findings lists the deferrals still open
`agentmarshal report --findings` SHALL print, for the tasks in scope,
the `deferred` entries of `advisory_dispositions` on `completed`
records still open — a deferral is open while its `follow_up` names no
task or names a task the journal does not hold as completed —
`load_task_status` answering which, its failure answering "not held by
the journal" rather than raising. Each open deferral SHALL print one
`Deferrals` line with the task, the finding id, the `reason` and the
follow-up — `follow_up=<task> (state: <state>)` when the journal holds
the task, `follow_up=<task> (not held by the journal)` when it does
not, `follow_up=(none)` when the entry names none (ADR-0016 decision
1). A deferral whose follow-up the journal holds as `done` SHALL NOT
print, and `fixed` and `rejected` entries SHALL NOT print. With no
open deferrals the section SHALL print `Deferrals	(none)`.

#### Scenario: each open deferral prints task, finding id, reason and follow-up
- **WHEN** a `completed` record's `advisory_dispositions` carries an
  open `deferred` entry
- **THEN** one `Deferrals` line prints naming the task, the finding id,
  the reason and the follow-up

#### Scenario: a deferral naming no follow-up task is open
- **WHEN** a `deferred` entry carries no `follow_up`
- **THEN** it is open and its line prints `follow_up=(none)`

#### Scenario: a deferral whose follow-up the journal does not hold is open
- **WHEN** a `deferred` entry's `follow_up` names a task the journal
  does not hold
- **THEN** it is open and its line prints `follow_up=<task> (not held
  by the journal)`

#### Scenario: a deferral whose follow-up is held but not completed is open
- **WHEN** a `deferred` entry's `follow_up` names a task the journal
  holds in a state other than `done`
- **THEN** it is open and its line prints `follow_up=<task> (state:
  <state>)`

#### Scenario: a deferral whose follow-up the journal holds as completed is not open
- **WHEN** a `deferred` entry's `follow_up` names a task the journal
  holds with projected state `done`
- **THEN** the deferral is not open and no `Deferrals` line prints for
  it

#### Scenario: fixed and rejected entries are not deferrals
- **WHEN** `advisory_dispositions` carries `fixed` and `rejected`
  entries
- **THEN** no `Deferrals` line prints for them

#### Scenario: with no open deferrals the view says so
- **WHEN** `report --findings` runs and no open deferral exists
- **THEN** the deferrals section prints `Deferrals	(none)`

### Requirement: the findings view escapes every record value on display
Every value `report --findings` takes from a record — a class name, a
finding id, a task id, a reason, a follow-up — SHALL be escaped where
it is displayed, as every record value in the report is (ADR-0015
decision 5).

#### Scenario: a record value in the findings view is escaped on display
- **WHEN** a class name, finding id, reason or follow-up the view prints
  carries a character that could forge a line
- **THEN** it prints escaped on the line
