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
`model`, `trace`, `cli_session`, `report_ready` and `fallback_reason`.
A session recorded with any of them SHALL be stamped schema 7, as any
record carrying the family is; a session recorded with none of them
SHALL keep the schema it had. A flag value the record rules refuse —
an empty or whitespace-only string, a forgeable character — SHALL be
refused with the record rule's message and no record SHALL be written.
`--outcome` SHALL remain free text, unconstrained by the flags.

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
