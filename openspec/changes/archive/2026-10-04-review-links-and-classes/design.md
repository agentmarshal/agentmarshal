## Context

ADR-0022 section 2 names the fields, and CR-154 laid down how a field
family registers: a `_FIELD_FAMILIES` entry ((schema, record type,
fields) — the `fields` rule computes the admitted set from the record's
own schema), the shared validator tables keyed by (record type, field),
a shape rule of the family's own bound to the schema it guards, and the
minimum-schema derivation. CR-160 registered the session family through
it and CR-173 the acceptance family. Two of the three fields are
top-level fields of the record; the third — `reviewer.actor` — is a key
inside the `reviewer` object, which the schema-1 `review` rule's
closed-key check guards, so it joins the family by that check admitting
it under the record's own schema while its shape is checked beside the
family's.

## Goals

- From schema 7 a `review` record may carry `previous_review`,
  `classes` and `reviewer.actor`; below 7 each is refused at write and
  on read.
- Registration follows the CR-154 mechanism exactly — the field family,
  the shared validator tables, the family's own schema-bound rule and
  the minimum-schema derivation — never a second mechanism.
- A review carrying none of them is validated and stamped exactly as
  before; no other record type changes and nothing reads the fields
  yet.

## Non-Goals

- The `review` launcher writing the fields, mapping a class to `other`
  with a warning, or resolving `previous_review` against the journal —
  later tasks, as is every reader (`status`, `report --findings`, the
  gate's independence rules).
- Recomputing or backfilling existing review records.

## Decisions

- **The family is `(7, "review", _SCHEMA_7_REVIEW_FIELDS)` with
  `{"previous_review", "classes"}`** — the two top-level fields.
  `reviewer.actor` is a key of the `reviewer` object, not of the
  record, so the frozenset does not name it and the `fields` rule never
  sees it; below 7 the reviewer object's closed keys refuse it instead.
  `_RECORD_FIELDS` is untouched — the family joins by registration,
  not by widening the base set the type always carried.
- **`("review", "previous_review")` registers into
  `_FORGEABLE_TEXT_FIELDS`; `classes` and `reviewer.actor` cannot, and
  get the check inline.** `previous_review`'s ULID shape admits no
  character the forgeable-text rule refuses, so the entry stands beside
  the family's shape rule for completeness — the same completeness the
  session and check families' `commit` entries carry. `classes` is an
  object and `actor` a nested key: a table entry would fail-closed on
  the dict, and the table keys on top-level fields so it could never
  reach the nested string. Each therefore gets the same
  `_reject_control_characters` check inside the family's own rule — the
  way `accepted_pause`'s `extension` does.
- **The family's own shape rule, `review-fields-7`, is bound to 7** —
  as `session-fields-7`, `check-fields-7`, `acknowledgement-fields-7`
  and `acceptance-fields-7` are. It refuses a `previous_review` that is
  not a string in the form record ids take (`_is_ulid`'s rule — a
  26-character Crockford base32 ULID), a `classes` that is not an
  object or is empty, a `classes` key that is not a finding id the
  record names in `findings` or `advisory_findings`, a class value that
  is empty, all whitespace, not a string or carries a character the
  forgeable-text rule refuses, and a `reviewer.actor` that is empty,
  all whitespace, not a string or carries such a character. It
  registers after `acceptance-fields-7` — behind the `review` rule — so
  `findings`, `advisory_findings` and `reviewer` are known valid when
  it reads them; and below 7 a record carrying the fields has already
  met the `fields` rule's or the closed-key refusal, at write and on
  read alike.
- **The reviewer object's closed-key check admits `actor` from schema
  7 by the record's own schema.** `_validate_review_record` computes
  the admitted set as `{role, vendor, model, email}` plus `actor` when
  the record's own schema reaches 7. The `review` rule keeps its
  schema-1 binding — a rule bound to 7 could not refuse `actor` on a
  review stamped below 7 on read, and this way the object stays closed
  for every record, old or new. Only admission lives there: the value's
  own shape sits in `review-fields-7` with the family's.
- **`_minimum_schema` raises to 7 on either top-level field or on
  `reviewer.actor`.** The nested key is a clause of its own beside
  `record.keys() & _SCHEMA_7_REVIEW_FIELDS` — `record.keys()` never
  sees inside `reviewer`.
- **An empty `classes` object is refused.** A review with nothing
  classified carries no `classes`, the way `advisory_findings` and
  `artifacts` are omitted when empty — an empty object is a second way
  to say the same thing, and a writer emitting one has a bug worth
  refusing.
- **`create_review_record` accepts `previous_review`, `classes` and
  `reviewer_actor` as optional keyword arguments**, setting each only
  when supplied — an explicit empty `classes` lands on the record and
  is refused at write rather than silently dropped. A review built
  without them is byte-identical to today's.

## Risks

- [A review stamped below 7 carrying a family field reads fine] → it
  does not: the `fields` rule is bound to 1 and computes the admitted
  set from the record's own schema, so `previous_review` and `classes`
  meet the unsupported-fields refusal on read exactly as a schema-1
  record carrying `usage` does today; `actor` meets the closed-key
  refusal the same way.
- [A `classes` key naming a finding the record does not carry] →
  refused by `review-fields-7` against the record's own `findings` and
  `advisory_findings` — the set is inside the record, at hand at write
  and on read alike, so no placement the read side lacks is needed.
- [A reader predating schema 7 meets such a review] → intended by
  ADR-0022's upgrade rule: the schema check refuses the record, not a
  field it cannot read.
