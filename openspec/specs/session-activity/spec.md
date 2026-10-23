# session-activity Specification

## Purpose
What a session record can say about the kind of work it measures. An
activity vocabulary that has no word for the most expensive role in an
agent-driven loop turns three quarters of a task's cost into "other", which is
not accounting.

## Requirements

### Requirement: A session can be recorded as coordination
A session record SHALL accept `coordination` as its activity, beside
`implementation`, `review` and `other`: the work of the agent that writes the
contract, launches the implementer, reads the verdict and reports to the
operator. The vocabulary SHALL be defined once and read by every writer and
reader of session records.

#### Scenario: a coordinating session is recorded as such
- **WHEN** a session is recorded with the activity `coordination`
- **THEN** the record is written and validated, and its activity reads back as
  `coordination`

#### Scenario: an activity outside the vocabulary is still refused
- **WHEN** a session is recorded with an activity that is not in the
  vocabulary
- **THEN** it is refused and nothing is written

### Requirement: An older reader refuses a coordination session by its schema
A session record whose activity is `coordination` SHALL carry at least the
schema number that introduced the value — 6 — and 7 when it carries a field
of the schema-7 session family, and a record with any other activity SHALL
keep the schema it had unless a field of the schema-7 session family raises
it to 7. A reader that predates the value then refuses the record as an
unsupported schema rather than as a malformed field, and a journal that never
records coordination stays readable by it.

#### Scenario: coordination stamps the newer schema
- **WHEN** a session is recorded with the activity `coordination` carrying
  none of the schema-7 session fields
- **THEN** the record carries schema 6, the newer schema number the value
  introduced

#### Scenario: a coordination session carrying a schema-7 field carries 7
- **WHEN** a session is recorded with the activity `coordination` carrying
  a field of the schema-7 session family
- **THEN** the record carries schema 7

#### Scenario: other activities keep their schema
- **WHEN** a session is recorded with `implementation`, `review` or `other`
  carrying none of the schema-7 session fields
- **THEN** the record carries the same schema number as before this change

#### Scenario: a non-coordination session carrying a schema-7 field carries 7
- **WHEN** a session is recorded with `implementation`, `review` or `other`
  carrying a field of the schema-7 session family
- **THEN** the record carries schema 7

### Requirement: A session record can say what it produced and with what
From schema 7, a session record MAY carry `commit` — the commit the
implementer run produced, as exactly 40 lowercase hex characters; `model`
— a non-empty string naming the model the session ran; `trace` — a
non-empty string holding an external link to the run's trace, recorded and
never fetched; `cli_session` — a non-empty string naming the CLI session a
resume needs; `report_ready` — a boolean saying the run's report was
finished; and `fallback_reason` — a non-empty string saying why a run
moved down the fallback list, shown and never verified. Each field is
optional. Each of `commit`, `model`, `trace`, `cli_session` and
`fallback_reason` SHALL pass the forgeable-text rule registered for the
session record type and that field, and no length bound SHALL apply to
any of them.

#### Scenario: a session carrying the new fields is written and read back
- **WHEN** a session record carries `commit`, `model`, `trace`,
  `cli_session`, `report_ready` and `fallback_reason`
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: each new field is optional
- **WHEN** a session record carries none of the family's fields
- **THEN** it is written and validated, and none of them appears in it

#### Scenario: a commit that is not 40 lowercase hex is refused
- **WHEN** a session record's `commit` is not exactly 40 lowercase hex
  characters
- **THEN** it is refused and nothing is written

#### Scenario: an empty string field is refused
- **WHEN** a session record's `model`, `trace`, `cli_session` or
  `fallback_reason` is empty, all whitespace or is not a string
- **THEN** it is refused and nothing is written

#### Scenario: a report_ready that is not a boolean is refused
- **WHEN** a session record's `report_ready` is not a boolean
- **THEN** it is refused and nothing is written

#### Scenario: a string field that could forge a rendered line is refused
- **WHEN** a string field of the family carries a character that could add
  a line to rendered output or reorder it
- **THEN** the record is refused

### Requirement: The schema-7 session fields are refused below schema 7
A session record carrying any of `commit`, `model`, `trace`,
`cli_session`, `report_ready`, `fallback_reason`, `started_at`,
`ended_at`, `resets_at` or `cost` SHALL carry schema 7: a writer carrying
any of them stamps schema 7 through the minimum-schema derivation, and
none of the fields SHALL be admitted to a session record stamped below 7 —
refused at write, and on read by the field-admission rule of the record's
own schema, as every schema-gated field is. A session record carrying
none of them SHALL stamp the schema it stamps without the family: 3, or
6 for a coordination activity. The fields SHALL be declared through the
registrations the schema-7 session family uses — the field family, the
family's own schema-bound rule and the minimum-schema derivation — not by
a second mechanism. Nothing reads them yet.

#### Scenario: a session carrying a field of the family stamps schema 7
- **WHEN** a session is recorded carrying any of the family's fields
- **THEN** the record carries schema 7

#### Scenario: a field of the family on a session below schema 7 is refused at write
- **WHEN** a session record stamped below 7 carries a field of the family
- **THEN** it is refused and nothing is written

#### Scenario: a field of the family on a session below schema 7 is refused on read
- **WHEN** the journal holds a session record stamped below 7 that carries
  a field of the family
- **THEN** reading the task's records refuses it as an unsupported field

#### Scenario: a session without the family keeps its schema
- **WHEN** a session is recorded carrying none of the family's fields
- **THEN** it carries the schema it carried before the family existed —
  3, or 6 for a `coordination` activity

### Requirement: record-session writes the schema-7 session fields from flags
`agentmarshal record-session` SHALL accept, each optional,
`--commit <rev>`, `--model <name>`, `--trace <link>`,
`--cli-session <id>`, `--report-ready` and `--fallback-reason <text>`,
writing the matching field of the schema-7 session family — `commit`,
`model`, `trace`, `cli_session`, `report_ready` and `fallback_reason`;
the family's `started_at`, `ended_at`, `resets_at` and `cost` are
written from flags of their own. A session recorded with any of the
family's flags SHALL be stamped schema 7, as any record carrying the
family is; a session recorded with none of them SHALL keep the schema
it had. A flag value the record rules refuse — an empty or
whitespace-only string, a forgeable character — SHALL be refused with
the record rule's message and no record SHALL be written. `--outcome`
SHALL remain free text, unconstrained by the flags.

#### Scenario: a session recorded with the flags carries the fields
- **WHEN** `record-session` runs with `--commit`, `--model`, `--trace`,
  `--cli-session`, `--report-ready` and `--fallback-reason`
- **THEN** the record is written, and each matching field reads back as
  given

#### Scenario: the flags are optional
- **WHEN** `record-session` runs with none of the family's flags
- **THEN** the record is written and carries none of the family's
  fields

#### Scenario: a session recorded with a flag is stamped schema 7
- **WHEN** `record-session` runs with any of the family's flags
- **THEN** the record carries schema 7

#### Scenario: a session recorded without the flags keeps its schema
- **WHEN** `record-session` runs with none of the family's flags
- **THEN** the record carries the schema it carried before the flags
  existed — 3, or 6 for a `coordination` activity

#### Scenario: a refused flag value writes nothing
- **WHEN** a flag carries a value the record rules refuse — an empty or
  whitespace-only string, or a character that could forge a rendered
  line
- **THEN** the command refuses with the record rule's message and
  writes no record

#### Scenario: an outcome of free text is still recorded
- **WHEN** `--outcome` carries free text
- **THEN** it is recorded as given

### Requirement: --commit resolves in the repository the work is in
`--commit` SHALL accept any revision git accepts, resolved with
`git rev-parse --verify <rev>^{commit}` in the repository the work is in
— the project's own repository for an embedded journal, the host
repository for a sidecar — and the record SHALL carry the resolved
full 40-character id. A revision git cannot resolve SHALL be refused
with a message naming it, and no record SHALL be written.

#### Scenario: a revision resolves to the full commit id
- **WHEN** `record-session --commit` names a revision that resolves in
  the repository the work is in
- **THEN** the record's `commit` is the full 40-character id it
  resolves to

#### Scenario: in a sidecar the revision resolves in the host
- **WHEN** `record-session --commit` runs in a sidecar naming a
  revision only the host knows
- **THEN** the record's `commit` is the id the host resolves it to

#### Scenario: an unknown revision is refused naming it
- **WHEN** `--commit` names a revision git cannot resolve
- **THEN** the command refuses with a message naming the revision and
  writes no record

### Requirement: A session record can say when the session ran
From schema 7, a session record MAY carry `started_at` and `ended_at` —
the session's start and end — admitted only together, each a UTC
ISO-8601 timestamp by the rule `created_at` follows, with `ended_at`
never earlier than `started_at`. `created_at` keeps its meaning — the
moment the record is written — and SHALL NOT be derived from them.

#### Scenario: a session carrying its start and end is written and read back
- **WHEN** a session record carries `started_at` and `ended_at`, each a
  UTC ISO-8601 timestamp with the end not earlier than the start
- **THEN** it is written and validated, and both fields read back as given

#### Scenario: a start without an end, or an end without a start, is refused
- **WHEN** a session record carries `started_at` without `ended_at`, or
  `ended_at` without `started_at`
- **THEN** it is refused and nothing is written

#### Scenario: an end earlier than the start is refused
- **WHEN** a session record's `ended_at` is earlier than its `started_at`
- **THEN** it is refused and nothing is written

#### Scenario: an end equal to the start is admitted
- **WHEN** a session record's `ended_at` equals its `started_at`
- **THEN** it is written and validated, and both fields read back as given

#### Scenario: a session timestamp that is not a UTC ISO-8601 timestamp is refused
- **WHEN** a session record's `started_at`, `ended_at` or `resets_at` is
  not a string, is not an ISO-8601 timestamp, or carries a non-UTC offset
  or no offset
- **THEN** it is refused and nothing is written

#### Scenario: created_at stays the write time
- **WHEN** a session record carries `started_at` and `ended_at`
- **THEN** its `created_at` is the moment the record is written, derived
  from neither

### Requirement: A provider-limit session can carry the reset time
From schema 7, a session record whose `outcome` is `provider-limit` MAY
carry `resets_at` — when the provider's stated allowance resets — a UTC
ISO-8601 timestamp by the rule `created_at` follows. `resets_at` SHALL be
refused on a session with any other outcome.

#### Scenario: a provider-limit session carrying the reset time is written and read back
- **WHEN** a session record whose outcome is `provider-limit` carries
  `resets_at`, a UTC ISO-8601 timestamp
- **THEN** it is written and validated, and the field reads back as given

#### Scenario: resets_at on another outcome is refused
- **WHEN** a session record whose outcome is not `provider-limit` carries
  `resets_at`
- **THEN** it is refused and nothing is written

### Requirement: A session record can carry a cost
From schema 7, a session record MAY carry `cost` — an object with
exactly `amount`, `currency` and `source`. `amount` SHALL be a
non-negative decimal written as a string of digits with an optional
fractional part — `"0"`, `"12"`, `"0.42"`, never a JSON number, so a sum
is exact. `currency` SHALL be three uppercase ASCII letters. `source`
SHALL be one of `reported` and `estimated`. Each refusal SHALL name the
field and the key at fault.

#### Scenario: a session carrying a cost is written and read back
- **WHEN** a session record carries `cost` — `amount` a decimal string,
  `currency` three uppercase ASCII letters, `source` one of `reported`
  and `estimated`
- **THEN** it is written and validated, and the object reads back as given

#### Scenario: an amount that is not a decimal string is refused
- **WHEN** a `cost` object's `amount` is a JSON number, is negative or
  carries a sign or an exponent, or is a string that is not digits with
  an optional fractional part — a leading or trailing `.`, whitespace
- **THEN** it is refused, the refusal naming `cost` and `amount`, and
  nothing is written

#### Scenario: a currency that is not three uppercase ASCII letters is refused
- **WHEN** a `cost` object's `currency` is not exactly three uppercase
  ASCII letters — `usd`, `US`, `USDT` — or is not a string
- **THEN** it is refused, the refusal naming `cost` and `currency`, and
  nothing is written

#### Scenario: a source outside the vocabulary is refused
- **WHEN** a `cost` object's `source` is not `reported` or `estimated`,
  or is not a string
- **THEN** it is refused, the refusal naming `cost` and `source`, and
  nothing is written

#### Scenario: a cost that is not an object of exactly amount, currency and source is refused
- **WHEN** a session record's `cost` is not an object, carries a key
  beside `amount`, `currency` and `source`, or lacks one of them
- **THEN** it is refused and nothing is written

### Requirement: record-session writes the session times, reset and cost from flags
`agentmarshal record-session` SHALL accept, each optional,
`--started-at <ts>` and `--ended-at <ts>` — the session's start and
end, admitted together or not at all, each a UTC ISO-8601 timestamp by
the rule `created_at` follows, the end never earlier than the start —
`--resets-at <ts>` — the provider's stated reset time, admitted on a
`provider-limit` outcome alone — and `--cost-amount <amount>` with
`--cost-currency <code>` and `--cost-source reported|estimated` — a
cost, the three admitted together or not at all — writing `started_at`,
`ended_at`, `resets_at` and `cost` of the schema-7 session family
through `create_session_record`'s parameters. A session recorded with
any of them SHALL be stamped schema 7, as any record carrying the
family is. A flag value the record rules refuse — an unpaired time, an
end earlier than the start, a timestamp that is not a UTC ISO-8601
timestamp, a reset time on an outcome other than `provider-limit`, an
incomplete or malformed cost — SHALL be refused before writing, the
refusal naming the flag, and no record SHALL be written.

#### Scenario: a session recorded with the flags carries the fields
- **WHEN** `record-session` runs with `--started-at` and `--ended-at`,
  `--resets-at` on a `provider-limit` outcome, and `--cost-amount` with
  `--cost-currency` and `--cost-source`
- **THEN** the record is written, and each matching field reads back as
  given

#### Scenario: an unpaired time flag is refused naming the flag
- **WHEN** `--started-at` is given without `--ended-at`, or `--ended-at`
  without `--started-at`
- **THEN** the command refuses naming the missing flag's pair and
  writes no record

#### Scenario: an end earlier than the start is refused naming the flag
- **WHEN** `--ended-at` is earlier than `--started-at`
- **THEN** the command refuses naming the flag and writes no record

#### Scenario: a timestamp that is not a UTC ISO-8601 timestamp is refused naming the flag
- **WHEN** `--started-at`, `--ended-at` or `--resets-at` is not an
  ISO-8601 timestamp, or carries a non-UTC offset or no offset
- **THEN** the command refuses naming the flag and writes no record

#### Scenario: a reset time on another outcome is refused naming the flag
- **WHEN** `--resets-at` is given on an outcome other than
  `provider-limit`
- **THEN** the command refuses naming the flag and writes no record

#### Scenario: an incomplete cost group is refused naming the flags
- **WHEN** one or two of `--cost-amount`, `--cost-currency` and
  `--cost-source` are given without the rest
- **THEN** the command refuses naming the flags and writes no record

#### Scenario: a malformed cost value is refused naming the flag
- **WHEN** `--cost-amount` is not a decimal string of digits with an
  optional fractional part, `--cost-currency` is not three uppercase
  ASCII letters, or `--cost-source` is outside `reported` and
  `estimated`
- **THEN** the command refuses naming the flag and writes no record

#### Scenario: a session recorded with the flags is stamped schema 7
- **WHEN** `record-session` runs with any of the time, reset or cost
  flags
- **THEN** the record carries schema 7

### Requirement: --if-missing makes a repeated session write a no-op
`agentmarshal record-session --if-missing` SHALL write no record when
the task already holds a session record with the same `role`, `actor`
and `activity`: the match is on the task and those three fields,
exactly (ADR-0019 decision 6), and the command SHALL print one line
naming the existing record instead of a record path. With no matching
session the command SHALL write as usual.

#### Scenario: a repeat under the same task, role, actor and activity is a no-op naming the existing record
- **WHEN** `record-session --if-missing` runs and the task already
  holds a session record with the same `role`, `actor` and `activity`
- **THEN** no second record is written and the command prints one line
  naming the existing record

#### Scenario: a session under a different role, actor or activity is written
- **WHEN** `record-session --if-missing` runs and the task's sessions
  match on fewer than all of `role`, `actor` and `activity`
- **THEN** the record is written as usual

#### Scenario: the match is bound to the task
- **WHEN** `record-session --if-missing` runs on a task and a session
  with the same `role`, `actor` and `activity` exists only under a
  different task
- **THEN** the record is written as usual

#### Scenario: the match ignores every other field
- **WHEN** `record-session --if-missing` runs and the task holds a
  session with the same `role`, `actor` and `activity` but a different
  outcome, tokens, times or cost
- **THEN** the match still holds and no second record is written

#### Scenario: without a matching session the write happens as usual
- **WHEN** `record-session --if-missing` runs and the task holds no
  session with the same `role`, `actor` and `activity`
- **THEN** the record is written and its path printed as without the
  flag

### Requirement: without the new flags record-session is unchanged
Without `--started-at`, `--ended-at`, `--resets-at`, the cost flags or
`--if-missing`, `agentmarshal record-session` SHALL write and print
exactly what it wrote and printed before they existed.

#### Scenario: a session written with today's flags is the record the previous release wrote
- **WHEN** `record-session` runs with the flags the command already
  had and none of the new ones
- **THEN** the record — apart from its id and times — is byte-for-byte
  the record the command wrote before the flags existed, and every
  line the command prints is unchanged

### Requirement: report --task shows the task's lead-time phases
`agentmarshal report --task <id>` SHALL print, after the task line it
prints today, the task's lead-time boundaries in order — `opened` (the
`opened` record's `created_at`), `implementer` (the `started_at` of the
first session record whose `role` is `implementer`), `review` (the
first `review` record's `created_at`), `approval` (the first `review`
whose `verdict` is `approved`, its `created_at`) and `completed` (the
task's last `completed` record's `created_at`) — and the durations
between consecutive boundaries. A boundary the records cannot supply
SHALL print `unknown` where a record exists but lacks the time — a
first implementer session carrying no `started_at` — and `not yet`
where the event has no record; a session's `created_at` SHALL NOT
stand in for its `started_at` (ADR-0019 decision 2). A duration SHALL
print when both its boundaries carry a time, `not yet` when its later
boundary has no record, and `unknown` otherwise.

#### Scenario: every boundary's time prints, with the durations between them
- **WHEN** `report --task` runs for a task whose records supply every
  boundary
- **THEN** the task line prints first, unchanged, then a line naming
  each boundary's time in order and a line of the durations between
  consecutive boundaries

#### Scenario: an implementer session without started_at is an unknown boundary
- **WHEN** the first implementer session carries no `started_at`
- **THEN** the `implementer` boundary prints `unknown`, the spans on
  either side of it print `unknown`, and the session's `created_at`
  appears nowhere as a boundary

#### Scenario: a boundary without a record is not yet
- **WHEN** a task has no implementer session, no review, no approving
  review or no completion
- **THEN** the matching boundary prints `not yet`, and a span whose
  later boundary is the missing one prints `not yet`

### Requirement: report --task lists the task's review rounds
`agentmarshal report --task <id>` SHALL list the task's `review`
records in their stored order, each numbered, with its `verdict` and
the elapsed time since the previous review — since the first
implementer session's `started_at` for the first — the elapsed time
`unknown` where that start is unknown or absent.

#### Scenario: rounds list in order with verdicts and elapsed times
- **WHEN** `report --task` runs for a task with review records
- **THEN** each round prints in order with the review's verdict and the
  time since the previous review — since the first implementer start
  for the first

#### Scenario: a first round after an unknown start is unknown
- **WHEN** the first implementer session carries no `started_at`, or
  the task holds no implementer session
- **THEN** the first round's elapsed time prints `unknown`

### Requirement: report aggregates lead time over completed tasks
`agentmarshal report` without `--task` SHALL print, after what it
prints today, an aggregate over the tasks whose projected state is
`done`: the count whose lead time is fully known — every boundary of
the task's phase chain carrying a time — with the median and the
maximum lead time among them, the lead time being `completed` minus
`opened`, and the count of completed tasks whose lead time is unknown.
A task whose lead time is unknown SHALL be counted, never averaged in;
with no fully known lead time the median and maximum SHALL be absent.

#### Scenario: the aggregate prints after today's output
- **WHEN** `report` runs over completed tasks, some with a fully known
  lead time and some without
- **THEN** after what it prints today it prints the count of fully
  known lead times, their median and maximum, and the count of unknown
  lead times

#### Scenario: an unknown lead time is counted, never averaged in
- **WHEN** `report` runs over a completed task missing a boundary — an
  implementer session without `started_at`, no review or no approval
- **THEN** the task counts toward the unknown count and contributes
  nothing to the median or maximum

#### Scenario: with no fully known lead time the median and maximum are absent
- **WHEN** `report` runs and no completed task has a fully known lead
  time
- **THEN** the aggregate prints no median and no maximum

### Requirement: the new lines leave today's output first and unchanged
Every line `report` and `report --task` print today SHALL print first
and unchanged, the new lines appended after; every value the new lines
take from a record SHALL be escaped where it is displayed, as every
record value in the view is.

#### Scenario: today's output is the new output's prefix
- **WHEN** `report` or `report --task` runs
- **THEN** every line the command printed before this change prints
  first and unchanged, and the new lines follow

#### Scenario: a record value in the new lines is escaped on display
- **WHEN** a value the new lines take from a record carries a
  character that could forge a line
- **THEN** it is escaped on display, as every record value in the view
  is
