## MODIFIED Requirements

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

## ADDED Requirements

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
