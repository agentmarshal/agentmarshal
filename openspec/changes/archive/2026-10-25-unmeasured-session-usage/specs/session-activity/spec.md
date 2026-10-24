## ADDED Requirements

### Requirement: an unmeasured session reads as unmeasured
A session record whose every token count is zero and which carries no
`usage` block reads as unmeasured — the zeros a session recorded with
no measurement wrote (digest 044's finding), never the zeros a measured
run earned. `status` and `report` SHALL read this one way, through the
single definition the two views share: a session record, every count in
its `tokens` zero, and no `usage` key present. A session carrying a
`usage` block SHALL read as measured — its zeros are a recorded
measurement — and a session carrying any non-zero token count SHALL
read as measured even with no `usage` block. No record is written,
rewritten or revalidated: the distinction is a read on the records the
journal holds.

#### Scenario: zero tokens and no usage is unmeasured
- **WHEN** a session record's `tokens` are all zero and it carries no
  `usage` block
- **THEN** it reads as unmeasured in `status` and `report`

#### Scenario: a session with a usage block reads as today
- **WHEN** a session record's `tokens` are all zero and it carries a
  `usage` block
- **THEN** it reads as measured — the zeros are a recorded measurement

#### Scenario: a session with a non-zero token reads as today
- **WHEN** a session record carries a non-zero token count and no
  `usage` block
- **THEN** it reads as measured

### Requirement: `status` shows an unmeasured session's tokens as unmeasured
`agentmarshal status <task>` SHALL show, on an unmeasured session's
record line, its tokens as `unmeasured` — `- <id> session <created_at>
tokens=unmeasured` — never as zeros a reader would take for a free run.
A session that is not unmeasured SHALL keep the record line it prints
today — the record's id, its type and its `created_at` — and every
value the line takes from a record SHALL be escaped where it is
displayed, as every record value in the view is.

#### Scenario: an unmeasured session's tokens show as unmeasured
- **WHEN** `status <task>` lists an unmeasured session record
- **THEN** its record line shows `tokens=unmeasured` after the id, type
  and `created_at` it prints today

#### Scenario: a measured session's line is unchanged
- **WHEN** `status <task>` lists a session record carrying a `usage`
  block or a non-zero token count
- **THEN** its record line is byte-for-byte the line it prints today

### Requirement: report leaves unmeasured sessions out of the token sums and names them
The token sum `agentmarshal report --task <id>` prints on the task's
line, and the token sum `agentmarshal report` prints on the `Summary`
line, SHALL sum the measured sessions alone — an unmeasured session
contributes nothing. Wherever such a sum prints and the scope left
sessions out as unmeasured, the line SHALL carry `unmeasured=<n>` as
its last field — the count of sessions the sum left out; a scope
leaving none SHALL carry no `unmeasured` field.

#### Scenario: the task line names the unmeasured sessions it left out
- **WHEN** `report --task` runs for a task holding unmeasured sessions
- **THEN** the task line's `tokens=` sums the measured sessions alone
  and the line carries `unmeasured=<n>` as its last field

#### Scenario: the summary names the unmeasured sessions it left out
- **WHEN** `report` runs over a journal holding unmeasured sessions
- **THEN** the `Summary` line's `tokens=` sums the measured sessions
  alone and the line carries `unmeasured=<n>` as its last field

### Requirement: an unmeasured session counts in no cost sum or measured-session count
An unmeasured session SHALL be no counted member of the `Cost` sums'
scope: it is no `sessions_without_cost` session and no `Cost` line's
`unmeasured=<n>` counts it. A `cost` it records SHALL sum exactly as a
measured session's does — per currency and source, in plain decimal:
the sum holds the figure, and leaving it out would silently drop money
the journal holds (ADR-0019 decision 4). Only an unmeasured session
carrying no `cost` is left out of these sums — wherever `Cost` lines
print, such sessions SHALL be named by `unmeasured=<n>` as the line's
last field, the count of unmeasured sessions carrying no `cost` alone —
and a scope whose every session is unmeasured carrying no `cost` SHALL
print no `Cost` line at all: the count means sessions that ran measured
and carried no cost, not sessions that measured nothing.

#### Scenario: a task whose only session is unmeasured but records a cost prints its Cost lines as today
- **WHEN** `report --task` runs for a task whose only session is
  unmeasured and carries a `cost`
- **THEN** the `Cost` lines print exactly as they print for a session
  today — the currency sum holding the recorded amount and
  `sessions_without_cost` printing — and no `Cost` line carries an
  `unmeasured` field

#### Scenario: an unmeasured session's recorded cost joins the per-currency sums
- **WHEN** a task holds an unmeasured session carrying a `cost` beside
  sessions carrying their own
- **THEN** every `Cost` currency line's sum holds the unmeasured
  session's recorded amount exactly as a measured session's does, and
  no `Cost` line's `unmeasured=<n>` counts it

#### Scenario: an unmeasured session carrying no cost is left out of the cost sums and named
- **WHEN** a task holds an unmeasured session carrying no `cost` and
  `Cost` lines print
- **THEN** the session is in no sum and no `sessions_without_cost`
  count, and every `Cost` line carries `unmeasured=<n>` as its last
  field — the count of such sessions alone

#### Scenario: a task holding only unmeasured sessions carrying no cost prints no cost lines
- **WHEN** `report --task` runs for a task whose every session is
  unmeasured and carries no `cost`
- **THEN** no `Cost` line prints

#### Scenario: the aggregate sums a recorded cost and names the sessions left out
- **WHEN** `report` runs over a journal holding unmeasured sessions,
  some carrying `cost` and some not
- **THEN** the recorded costs sum per currency and source exactly as a
  measured session's does, and every `Cost` line carries
  `unmeasured=<n>` counting the unmeasured sessions carrying no `cost`
  alone

### Requirement: a journal holding no unmeasured session prints what it prints today
Every line `status` and `report` print for a journal holding no
unmeasured session SHALL be byte-for-byte what they printed before this
change; every value the new fields and lines take from a record SHALL
be escaped where it is displayed, as every record value in the view is.

#### Scenario: with no unmeasured session nothing changes
- **WHEN** `status` or `report` runs for a journal holding no
  unmeasured session
- **THEN** every line is byte-for-byte what the command printed before
  this change

## MODIFIED Requirements

### Requirement: the new lines leave today's output first and unchanged
Every line `report` and `report --task` print today SHALL print first
and, for a journal holding no unmeasured session, unchanged, the new
lines appended after; every value the new lines take from a record
SHALL be escaped where it is displayed, as every record value in the
view is. A journal holding an unmeasured session admits the one
exception the unmeasured-session requirements name: a line carrying a
sum those sessions were left out of gains `unmeasured=<n>` as its last
field and nothing more, and every other line prints unchanged.

#### Scenario: today's output is the new output's prefix
- **WHEN** `report` or `report --task` runs over a journal holding no
  unmeasured session
- **THEN** every line the command printed before this change prints
  first and unchanged, and the new lines follow

#### Scenario: the unmeasured field joins a sum line and the new lines still follow
- **WHEN** `report` or `report --task` runs over a journal holding an
  unmeasured session
- **THEN** every line the command printed before this change prints
  first — each line carrying a sum the session was left out of gaining
  `unmeasured=<n>` as its last field and nothing more — and the new
  lines follow

#### Scenario: a record value in the new lines is escaped on display
- **WHEN** a value the new lines take from a record carries a
  character that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is

### Requirement: report --task shows the task's cost per currency
`agentmarshal report --task <id>` SHALL print, after the round lines it
prints today, the task's `Cost` lines: one line per currency the task's
session `cost` objects sum to — a `cost` an unmeasured session recorded
summing exactly as a measured session's does — sorted by currency code,
carrying the `reported` and `estimated` sums separately —
`Cost	<currency> reported=<sum>` with `estimated=<sum>` when that
source is present — and a `Cost	sessions_without_cost=<n>` line
counting the task's measured sessions carrying no `cost`, printed
whenever the task holds at least one session the sums admit — a
measured session or one carrying a `cost`. Amounts SHALL be summed as
decimals and printed in plain decimal notation — never as floats. No
sum SHALL convert or blend currencies: two currencies are two lines,
never one figure (ADR-0019 decision 4). A task whose admitted sessions
carry no cost SHALL print no currency line — none rather than zero —
and a task holding no session the sums admit SHALL print no `Cost`
line at all. Every `Cost` line SHALL carry `unmeasured=<n>` as its
last field whenever the task holds unmeasured sessions carrying no
`cost` — the count of those sessions alone.

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
- **WHEN** the task holds measured sessions, some carrying `cost` and
  some not
- **THEN** `Cost	sessions_without_cost=<n>` prints the count of the
  task's measured sessions carrying no `cost`

#### Scenario: a task holding no session prints no cost lines
- **WHEN** `report --task` runs for a task holding no session record
- **THEN** no `Cost` line prints

### Requirement: report aggregates cost per currency
`agentmarshal report` without `--task` SHALL print, after the `Lead`
line it prints today, the same sums over every task's sessions: one
`Cost` line per currency carrying `reported` and `estimated` apart —
a `cost` an unmeasured session recorded summing exactly as a measured
session's does — and a `Cost	sessions_without_cost=<n>` line counting
every measured session carrying no `cost` whenever the journal holds at
least one session the sums admit — a measured session or one carrying a
`cost`. A journal whose admitted sessions carry no cost SHALL print no
currency line — none rather than zero. Every `Cost` line SHALL carry
`unmeasured=<n>` as its last field whenever the journal holds
unmeasured sessions carrying no `cost` — the count of those sessions
alone.

#### Scenario: the aggregate sums every task's sessions per currency and source
- **WHEN** `report` runs over tasks whose sessions carry `cost`
- **THEN** after the `Lead` line, one `Cost` line per currency prints
  the `reported=` and `estimated=` sums over every task's sessions

#### Scenario: no conversion or blending across currencies in the aggregate
- **WHEN** `report` runs over sessions carrying costs in two currencies
- **THEN** two `Cost` lines print, one per currency, and no line
  combines them

#### Scenario: the aggregate counts sessions carrying no cost
- **WHEN** `report` runs over a journal holding measured sessions
  without `cost`
- **THEN** `Cost	sessions_without_cost=<n>` prints their count

#### Scenario: with no cost recorded the aggregate prints no currency line
- **WHEN** `report` runs over a journal whose sessions carry no `cost`,
  or none at all
- **THEN** no `Cost` currency line prints

### Requirement: the cost and check lines leave today's output first and unchanged
Every line `report` and `report --task` print today SHALL print first
and, for a journal holding no unmeasured session, unchanged, the cost
and check lines appended after; every value the new lines take from a
record SHALL be escaped where it is displayed, as every record value in
the view is (ADR-0015 decision 5). A journal holding an unmeasured
session admits the one exception the unmeasured-session requirements
name: a line carrying a sum those sessions were left out of gains
`unmeasured=<n>` as its last field and nothing more, and every other
line prints unchanged.

#### Scenario: today's report output is the new output's prefix
- **WHEN** `report` or `report --task` runs over a journal holding no
  unmeasured session
- **THEN** every line the command printed before this change prints
  first and unchanged, and the cost and check lines follow

#### Scenario: the unmeasured field joins a sum line and the cost and check lines still follow
- **WHEN** `report` or `report --task` runs over a journal holding an
  unmeasured session
- **THEN** every line the command printed before this change prints
  first — each line carrying a sum the session was left out of gaining
  `unmeasured=<n>` as its last field and nothing more — and the cost
  and check lines follow

#### Scenario: a record value in the cost or check lines is escaped on display
- **WHEN** a value the new lines take from a record carries a
  character that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is

### Requirement: the session line leaves today's output unchanged and escapes record values
Every line `agentmarshal status <task>` prints today SHALL print
unchanged — a journal holding an unmeasured session admitting the one
exception the unmeasured-session requirements name: an unmeasured
session's record line gains ` tokens=unmeasured` after the
`created_at` it prints today and nothing more, every other line
unchanged — the session line appended after; every value the line
takes from a record SHALL be escaped where it is displayed, as every
record value in the view is; the line SHALL refuse and block nothing.

#### Scenario: today's lines print unchanged and the session line follows
- **WHEN** `status <task>` runs for a task the line answers for and
  which holds no unmeasured session
- **THEN** every line the command printed before this change prints
  unchanged, and the session line follows

#### Scenario: an unmeasured session's record line gains the unmeasured mark and nothing more
- **WHEN** `status <task>` runs for a task holding an unmeasured
  session
- **THEN** every line the command printed before this change prints
  unchanged but the session's record line — ` tokens=unmeasured` after
  the `created_at` it prints today and nothing more — and the session
  line follows

#### Scenario: a record value on the session line is escaped on display
- **WHEN** a value the line takes from a record carries a character
  that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is
