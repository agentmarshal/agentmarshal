## MODIFIED Requirements

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

## ADDED Requirements

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
