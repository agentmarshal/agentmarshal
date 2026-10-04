## Context

ADR-0022 section 2 names the field, and CR-154 laid down how a field
family registers: a `_FIELD_FAMILIES` entry ((schema, record type,
fields) — the `fields` rule computes the admitted set from the record's
own schema), the shared validator tables keyed by (record type, field),
a shape rule of the family's own bound to the schema it guards, and the
minimum-schema derivation. CR-160 registered the session family through
it, CR-173 the acceptance family — whose new forms bind by
`accepted_commit` alone, a binding-dependent refusal — and CR-174 the
review family, whose `classes` is an object with per-key validation. This
field is the two shapes combined: an object whose values are objects, on
a record type with two bindings, admitted on one of them.

## Goals

- From schema 7 a `completed` record bound by `completed_commit` may
  carry `advisory_dispositions`; on `completed_finding` it is refused,
  and below 7 it is refused at write and on read.
- Registration follows the CR-154 mechanism exactly — the field family,
  the family's own schema-bound rule and the minimum-schema derivation —
  never a second mechanism.
- A `completed` record without the field is validated and stamped
  exactly as before; no other record type changes and nothing reads the
  field yet.

## Non-Goals

- `complete --disposition`, the refusal when an advisory finding lacks a
  disposition, and checking the keys against the review's advisory
  findings — they need the journal; later tasks — as are `status` and
  `report` showing open deferrals.
- A length bound on `reason` — ADR-0022 section 8 sets none for this
  field.
- Recomputing or backfilling existing `completed` records.

## Decisions

- **The family is `(7, "completed", _SCHEMA_7_COMPLETED_FIELDS)` with
  `{"advisory_dispositions"}`.** `_RECORD_FIELDS["completed"]` is
  untouched — the family joins by registration, not by widening the base
  set the type always carried; below 7 the `fields` rule refuses the
  field at write and, on read, under the record's own schema.
- **The family's own shape rule, `completed-fields-7`, is bound to 7** —
  as `session-fields-7`, `check-fields-7`, `acknowledgement-fields-7`,
  `acceptance-fields-7` and `review-fields-7` are. It registers after
  `review-fields-7` — behind the `completed` rule — so the binding is
  known valid when it reads it: one of `completed_commit`,
  `completed_finding`, never both. It refuses the field on a
  finding-bound completion first — `complete --findings` takes no
  dispositions (ADR-0016 decision 1), the refusal the acceptance family's
  `accepted_finding` check is the model for — then an
  `advisory_dispositions` that is not an object or is empty, a key that
  is not a non-empty finding id passing the rule finding ids pass (the
  same non-empty-string and `_reject_control_characters` the review's
  `findings` apply), an entry that is not an object, an entry carrying a
  key outside `disposition`, `reason` and `follow_up`, a `disposition`
  outside `fixed`, `deferred` and `rejected`, a `reason` missing on
  `deferred` or `rejected` or present but empty or not a string, and a
  `follow_up` on `fixed` or `rejected` or one that is not a task id in
  the form task ids take — the `CR-<number>` rule `open` assigns and
  `validate_task_id` applies, replicated rather than imported because
  `records.py` already carries the pattern. Every refusal names the
  finding id and the key at fault — the coordinator supplying the
  dispositions answers finding by finding.
- **`reason` and `follow_up` take the forgeable-text check inside the
  family's own rule.** `advisory_dispositions` is an object whose values
  are objects: a `_FORGEABLE_TEXT_FIELDS` entry would fail-closed on the
  dict, and a top-level key could never reach the nested strings — the
  same twice-nested case CR-174's `classes` values were, so each gets
  the same `_reject_control_characters` check for exactly this record
  type and field, as `accepted_pause`'s `extension` does. `follow_up`'s
  `CR-<number>` shape admits no character the rule refuses either way;
  the check stands ahead of the shape check the way `extension`'s does.
  The limit tables gain no entry: ADR-0022 section 8 bounds `excerpt`,
  `payload` and the new record types' `reason` alone — the `reason`
  nested here is a completed record's, not a new record type's.
- **An empty `advisory_dispositions` is refused.** A completion with
  nothing answered carries no field, the way `advisory_findings` and
  `classes` are omitted when empty — an empty object is a second way to
  say the same thing, and a writer emitting one has a bug worth
  refusing.
- **`_minimum_schema` raises to 7 on `advisory_dispositions`**, a clause
  beside the other schema-7 families'.
- **`create_completed_record` accepts `advisory_dispositions` as an
  optional keyword argument**, set only when supplied — an explicit
  empty object lands on the record and is refused at write rather than
  silently dropped — and refuses the field with `completed_finding` up
  front, the same refusal `create_acceptance_record` gives a new form
  bound by `accepted_finding`. A record built without it is
  byte-identical to today's.

## Risks

- [A `completed` record stamped below 7 carrying the field reads fine] →
  it does not: the `fields` rule is bound to 1 and computes the admitted
  set from the record's own schema, so the field meets the
  unsupported-fields refusal on read exactly as a schema-1 record
  carrying `usage` does today.
- [A disposition key naming a finding the review never raised] → not the
  record's check: which findings the review raised lives in the journal,
  and the key-matching task is a later one — the record checks only that
  each key is a well-formed finding id.
- [A `reason` bound creeping in through the shared tables] → the bound
  ADR-0022 section 8 gives `reason` is for the new record types and keys
  on record type; no registration names `completed`, so the field here
  carries no bound — the ADR sets none.
- [A reader predating schema 7 meets such a record] → intended by
  ADR-0022's upgrade rule: the schema check refuses the record, not a
  field it cannot read.
