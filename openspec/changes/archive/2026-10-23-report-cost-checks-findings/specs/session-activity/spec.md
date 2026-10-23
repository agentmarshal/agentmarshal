## ADDED Requirements

### Requirement: report --task shows the task's cost per currency
`agentmarshal report --task <id>` SHALL print, after the round lines it
prints today, the task's `Cost` lines: one line per currency the task's
session `cost` objects sum to, sorted by currency code, carrying the
`reported` and `estimated` sums separately — `Cost	<currency>
reported=<sum>` with `estimated=<sum>` when that source is present —
and a `Cost	sessions_without_cost=<n>` line counting the task's
sessions carrying no `cost`, printed whenever the task holds at least
one session. Amounts SHALL be summed as decimals and printed in plain
decimal notation — never as floats. No sum SHALL convert or blend
currencies: two currencies are two lines, never one figure (ADR-0019
decision 4). A task whose sessions carry no cost SHALL print no
currency line — none rather than zero — and a task holding no session
SHALL print no `Cost` line at all.

#### Scenario: cost sums print per currency with reported and estimated apart
- **WHEN** `report --task` runs for a task whose sessions carry `cost`
- **THEN** one `Cost` line prints per currency — after the task's round
  lines — carrying `reported=` and `estimated=` sums separately, each a
  decimal

#### Scenario: two currencies are two sums, never a blended figure
- **WHEN** the task's sessions carry costs in two currencies
- **THEN** two `Cost` lines print, one per currency, and no line
  combines them

#### Scenario: amounts sum and print as decimals, never floats
- **WHEN** the task's sessions carry costs whose amounts do not sum
  exactly in binary floating point — `1.10` and `2.20`
- **THEN** the printed sum is `3.30`, the exact decimal

#### Scenario: a task with no cost shows none rather than zero
- **WHEN** the task's sessions carry no `cost`
- **THEN** no `Cost` currency line prints — none rather than a zero sum

#### Scenario: the count of sessions carrying no cost prints
- **WHEN** the task holds sessions, some carrying `cost` and some not
- **THEN** `Cost	sessions_without_cost=<n>` prints the count of the
  task's sessions carrying no `cost`

#### Scenario: a task holding no session prints no cost lines
- **WHEN** `report --task` runs for a task holding no session record
- **THEN** no `Cost` line prints

### Requirement: report aggregates cost per currency
`agentmarshal report` without `--task` SHALL print, after the `Lead`
line it prints today, the same sums over every task's sessions: one
`Cost` line per currency carrying `reported` and `estimated` apart,
and a `Cost	sessions_without_cost=<n>` line counting every session
carrying no `cost` whenever the journal holds at least one session. A
journal with no cost recorded SHALL print no currency line — none
rather than zero.

#### Scenario: the aggregate sums every task's sessions per currency and source
- **WHEN** `report` runs over tasks whose sessions carry `cost`
- **THEN** after the `Lead` line, one `Cost` line per currency prints
  the `reported=` and `estimated=` sums over every task's sessions

#### Scenario: no conversion or blending across currencies in the aggregate
- **WHEN** `report` runs over sessions carrying costs in two currencies
- **THEN** two `Cost` lines print, one per currency, and no line
  combines them

#### Scenario: the aggregate counts sessions carrying no cost
- **WHEN** `report` runs over a journal holding sessions without `cost`
- **THEN** `Cost	sessions_without_cost=<n>` prints their count

#### Scenario: with no cost recorded the aggregate prints no currency line
- **WHEN** `report` runs over a journal whose sessions carry no `cost`,
  or none at all
- **THEN** no `Cost` currency line prints

### Requirement: report counts the commits the pipeline rejected
`agentmarshal report --task <id>` SHALL print, next to the review
rounds — after the `Cost` lines, as "next to rounds and cost" reads —
a `Checks	rejected_commits=<n>` line counting the task's distinct
commits a `check` record marked `failed` or `error`; `passed` and
`skipped` SHALL NOT count, and two records on one commit SHALL count
once — the count is of rejected candidates, not records (ADR-0017
decision 3). `agentmarshal report` without `--task` SHALL print the
same line in aggregate after the `Cost` lines — the total over tasks —
and, wherever the `Checks` line prints, the report SHALL say once that
a check record is the observer's declaration of what the pipeline found
on the commit, not proof of it (ADR-0017 decision 2).

#### Scenario: the per-task count prints next to the review rounds
- **WHEN** `report --task` runs for a task holding `check` records
  marked `failed` or `error`
- **THEN** it prints `Checks	rejected_commits=<n>` after the task's
  round and cost lines — the count of distinct commits the records name

#### Scenario: distinct commits are counted, not records
- **WHEN** a task holds two `check` records marked `failed` or `error`
  on one commit and one on another
- **THEN** the count is two — the distinct commits — not three records

#### Scenario: failed and error count; passed and skipped do not
- **WHEN** a task holds `check` records of every result
- **THEN** only commits a record marked `failed` or `error` count toward
  `rejected_commits`

#### Scenario: the aggregate counts every task's rejected commits
- **WHEN** `report` runs over tasks holding `check` records marked
  `failed` or `error`
- **THEN** after the `Cost` lines it prints `Checks	rejected_commits=<n>`
  — the total over tasks of each task's distinct count

#### Scenario: the report says once that a check record is the observer's declaration
- **WHEN** `report` or `report --task` runs
- **THEN** the output carries, once, that a check record is the
  observer's declaration of what the pipeline found on the commit, not
  proof of it

### Requirement: the cost and check lines leave today's output first and unchanged
Every line `report` and `report --task` print today SHALL print first
and unchanged, the cost and check lines appended after; every value the
new lines take from a record SHALL be escaped where it is displayed, as
every record value in the view is (ADR-0015 decision 5).

#### Scenario: today's report output is the new output's prefix
- **WHEN** `report` or `report --task` runs
- **THEN** every line the command printed before this change prints
  first and unchanged, and the cost and check lines follow

#### Scenario: a record value in the cost or check lines is escaped on display
- **WHEN** a value the new lines take from a record carries a character
  that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is
