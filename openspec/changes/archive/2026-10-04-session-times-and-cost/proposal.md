## Why

ADR-0019 decides what the journal records about a session's time and
money: its start and end, beside `created_at`, which stays the write time
(decision 1); the provider's stated reset time on a `provider-limit`
session (decision 3); and an optional cost — an amount, a currency and
its source, `reported` or `estimated`, summed per currency and never
converted (decision 4). ADR-0022 section 2 names the fields in schema 7:
`started_at`, `ended_at`, `resets_at`, `cost`. ADR-0019 leaves the
amount's form open; this change fixes it as a decimal string so `report`
can sum it exactly. CR-154 laid down the registry a field family declares
through, and CR-160 registered the first six fields of the same session
family through it; a session today still cannot say when it ran, when its
provider's allowance resets, or what it cost.

## What Changes

- A session record may carry, from schema 7 only: `started_at` and
  `ended_at` — admitted only together, each a UTC ISO-8601 timestamp by
  the rule `created_at` follows, the end never earlier than the start —
  and `resets_at`, the same timestamp admitted only on a `provider-limit`
  outcome, and `cost` — an object of exactly `amount`, a non-negative
  decimal written as a string of digits with an optional fractional part
  (`"0"`, `"12"`, `"0.42"`, never a JSON number), `currency`, three
  uppercase ASCII letters, and `source`, `reported` or `estimated` — each
  refusal naming the field and the key at fault.
- Any of the four on a session stamped below 7 is refused at write and,
  on read, by the field-admission rule of the record's own schema; a
  writer carrying any of them stamps 7 through the minimum-schema
  derivation; a session carrying none is validated and stamped exactly as
  before — 3, or 6 for coordination.
- `create_session_record` accepts the four as optional keyword arguments.
- The family's enumeration in `session-activity`'s below-7 requirement
  becomes untrue — a session carrying `cost` but none of the six named
  fields would still stamp 7 — so the requirement is modified in place
  under its exact header.

## Capabilities

- modified: `session-activity`

## Impact

No other record type changes and the gate's fixtures are unchanged. The
fields are write-side only for now: nothing reads them yet — the
`record-session` flags that set them, `--if-missing`, and `report`'s
lead time, phases and cost sums are later tasks.
