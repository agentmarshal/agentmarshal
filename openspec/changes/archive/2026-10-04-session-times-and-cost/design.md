## Context

CR-154 laid down how a field family registers — a `_FIELD_FAMILIES`
entry ((schema, record type, fields) — the `fields` rule computes the
admitted set from the record's own schema), the shared validator tables
keyed by (record type, field), a shape rule of the family's own bound to
the schema it guards, and the minimum-schema derivation. CR-160
registered the session family's first six fields through it — one
frozenset, one `_FIELD_FAMILIES` entry, the `session-fields-7` shape
rule — and CR-175's `advisory_dispositions` is the model for an
object-valued field whose refusals name the key at fault. This change
adds the four remaining session fields of ADR-0022 section 2 — the times
and the cost ADR-0019 decisions 1, 3 and 4 decided — to that same
family.

## Goals

- A session record may carry `started_at`/`ended_at` (only together),
  `resets_at` (on `provider-limit` alone) and `cost` under schema 7, and
  nothing older changes.
- Declaration follows the family's existing registrations exactly — the
  one frozenset, the one `_FIELD_FAMILIES` entry, the family's own rule,
  the one minimum-schema clause — never a second mechanism.

## Non-Goals

- `record-session` flags for the fields, `--if-missing`, and `report`'s
  lead time, phases and cost sums — later tasks.
- Any check that a cost's figure is true, or any conversion between
  currencies (ADR-0019 decision 4).

## Decisions

- **The four fields join `_SCHEMA_7_SESSION_FIELDS` itself.** One
  frozenset, the existing `(7, "session", …)` `_FIELD_FAMILIES` entry
  and the existing `record.keys() & _SCHEMA_7_SESSION_FIELDS` clause in
  `_minimum_schema` — so admission, the below-7 refusal and the stamp
  need no new mechanism: the family is ten fields, not two families.
  Below 7 the `fields` rule refuses them at write and, on read, under
  the record's own schema, exactly as `usage` is refused on a schema-1
  session.
- **`created_at`'s UTC ISO-8601 rule is factored out and reused.** The
  `created-at` rule's parse — `fromisoformat` after the `Z` → `+00:00`
  rewrite, then the offset-must-be-UTC check — becomes `_utc_timestamp`,
  taking the field name a refusal gives; `session-fields-7` calls it for
  `started_at`, `ended_at` and `resets_at`, so there is one timestamp
  parser, not two. `created_at` keeps its meaning — the write time —
  and is derived from none of them.
- **The family's own rule gains the shapes no shared validator covers —
  still `session-fields-7`, still bound to 7.** It refuses a `started_at`
  without `ended_at` and the reverse, an `ended_at` earlier than
  `started_at` (equal admitted), a `resets_at` on any outcome but
  `provider-limit` — `outcome` stays free text and the gate keys on the
  documented word, as ADR-0022 section 4 names it — and a `cost` that is
  not an object of exactly `amount`, `currency`, `source`: an `amount`
  that is not `[0-9]+(\.[0-9]+)?`, a `currency` that is not `[A-Z]{3}`,
  a `source` outside `reported` and `estimated`. Each `cost` refusal
  names the field and the key at fault, as the `usage` object's checks
  already do.
- **The amount is a decimal string, never a JSON number.** ADR-0019 left
  the form open and the contract fixes it as a string of digits with an
  optional fractional part, so `report`'s per-currency sum is exact — a
  JSON float `0.42` is not. The pattern refuses the JSON-number forms,
  a sign, an exponent, a leading or trailing `.` and whitespace; `"0"`,
  `"12"` and `"0.42"` are admitted.
- **No new field registers in the shared validator tables.** The
  timestamps and each `cost` key are closed shapes — an ISO-8601 UTC
  timestamp, a digit string, three uppercase ASCII letters, a two-word
  vocabulary — each admitting no character the forgeable-text rule
  refuses, and `session-fields-7` runs ahead of that rule, so an entry
  would never fire. It is the same reason the acknowledgement family's
  `signature` vocabulary and `marker`'s integer shape carry none, and
  it keeps the threat model's enumeration of the family's registered
  fields — the five displayed strings — true. The limit tables gain no
  entry either: ADR-0022 section 8 bounds `excerpt`, `payload` and the
  new record types' `reason` alone.
- **`create_session_record` accepts the four as optional keyword
  arguments**, set only when supplied — the family fields' own pattern —
  so a session without them is byte-identical to today's. The builder
  passes the values through unchecked: the record rules own every
  refusal, as they do for `commit`.

## Risks

- [A session stamped below 7 carrying one of the four reads fine] → it
  does not: the `fields` rule is bound to 1 and computes the admitted
  set from the record's own schema, so the field meets the
  unsupported-fields refusal on read exactly as a schema-1 record
  carrying `usage` does today.
- [`created_at` drifting into the session's start] → it stays the write
  time: the fields are declared, never derived — `create_session_record`
  keeps setting `created_at` to now and no reader substitutes it, the
  substitution ADR-0019 decision 2 forbids.
- [A `resets_at` refused on a documented-but-unchecked outcome] →
  intended: `outcome` stays free text by ADR-0019 decision 5, and the
  field gate keys on the exact word `provider-limit` — the value
  ADR-0022 section 4 says carries it.
- [A reader predating schema 7 meets such a session] → intended by
  ADR-0022's upgrade rule: the schema check refuses the record, not a
  field it cannot read.
