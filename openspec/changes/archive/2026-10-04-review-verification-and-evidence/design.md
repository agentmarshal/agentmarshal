## Context

ADR-0022 section 2 names the fields, and CR-174 laid down how a review
field family registers: the `_SCHEMA_7_REVIEW_FIELDS` frozenset in the
`_FIELD_FAMILIES` entry `(7, "review", …)` — the `fields` rule computes
the admitted set from the record's own schema — the shared validator
tables keyed by (record type, field), the family's own rule
`review-fields-7` bound to 7, and the minimum-schema derivation. Two of
this family's new fields are top-level fields of the record, like
`previous_review` and `classes` before them; both are objects, which is
the case `classes` already covered — a forgeable-text table entry would
fail-closed on the dict, so the strings inside take the check inline.

## Goals

- From schema 7 a `review` record may carry `verification` and
  `evidence`; below 7 each is refused at write and on read.
- Registration follows the CR-154 mechanism exactly — the same field
  family entry, the family's own schema-bound rule and the
  minimum-schema derivation — never a second mechanism; `evidence`
  keys bind by the one named-finding check `classes` uses, not a second
  one.
- A review carrying neither field is validated and stamped exactly as
  before; no other record type changes and nothing reads or writes the
  fields yet.

## Non-Goals

- The review protocol lines that ask the reviewer for the sections, the
  launcher writing the fields, the "unconfirmed" advisory line of
  ADR-0017 decision 5, and every reader — later tasks.
- `mode: resolution` and `carried_approval` (blocked pending the review
  of the queue model).
- A length bound on either field — ADR-0022 section 8 sets none for
  them.

## Decisions

- **The family frozenset grows to `{"previous_review", "classes",
  "verification", "evidence"}`.** The `_FIELD_FAMILIES` entry
  `(7, "review", …)` admits all four top-level fields from schema 7 by
  the record's own schema; `_RECORD_FIELDS` is untouched — the family
  joins by registration, not by widening the base set the type always
  carried. `_minimum_schema` needs no new clause:
  `record.keys() & _SCHEMA_7_REVIEW_FIELDS` already covers both fields.
- **Neither field registers in `_FORGEABLE_TEXT_FIELDS`; every string
  inside gets the check inline.** Both are objects — a table entry
  would fail-closed on the dict, exactly as it would for `classes` — so
  `verification`'s `what`/`result`/`why`/`read` strings and `evidence`'s
  values take the same `_reject_control_characters` check inside the
  family's own rule `review-fields-7`, as `accepted_pause`'s `extension`
  does.
- **The `evidence` key check is the `classes` key check.** The set a
  key may name — the finding ids the record itself carries in
  `findings` or `advisory_findings`, inside the record at write and on
  read alike — is computed once by `_check_review_keyed_field`, which
  both fields call; the refusal names the field and the key at fault.
- **`review-fields-7` checks the new fields beside the family's.**
  Bound to 7 as it is, it refuses a `verification` that is not an
  object, is empty, or carries a key outside `executed`, `read` and
  `not_run`; a section that is not a non-empty array; an `executed` or
  `not_run` entry that is not an object or misses or adds a key; a
  `read` item that is not a string; and any string inside that is empty,
  all whitespace or carries a character the forgeable-text rule refuses
  — each refusal naming the section, the position and the key at fault.
  It refuses an `evidence` that is not an object or is empty, a key
  naming no finding of the record, and a value that is empty, all
  whitespace, not a string or forgeable — the refusal naming the key.
  The rule already runs behind the `review` rule, so `findings`,
  `advisory_findings` and `reviewer` are known valid when it reads them;
  below 7 a record carrying either field has already met the `fields`
  rule's refusal, at write and on read alike.
- **An empty `verification` object and an empty `evidence` object are
  refused.** A review with nothing executed, read or left unrun carries
  no `verification`; one with no evidence to name carries no `evidence`
  — the way `classes`, `advisory_findings` and `artifacts` are omitted
  when empty: an empty object is a second way to say the same thing, and
  a writer emitting one has a bug worth refusing.
- **`create_review_record` accepts `verification` and `evidence` as
  optional keyword arguments**, setting each only when supplied — an
  explicit empty object lands on the record and is refused at write
  rather than silently dropped. A review built without them is
  byte-identical to today's.

## Risks

- [A review stamped below 7 carrying either field reads fine] → it does
  not: the `fields` rule is bound to 1 and computes the admitted set
  from the record's own schema, so both meet the unsupported-fields
  refusal on read exactly as `previous_review` and `classes` do.
- [An `evidence` key naming a finding the record does not carry] →
  refused by `review-fields-7` through the same `_check_review_keyed_field`
  `classes` uses — the set is inside the record, at hand at write and on
  read alike, so no placement the read side lacks is needed.
- [A reader predating schema 7 meets such a review] → intended by
  ADR-0022's upgrade rule: the schema check refuses the record, not a
  field it cannot read.
