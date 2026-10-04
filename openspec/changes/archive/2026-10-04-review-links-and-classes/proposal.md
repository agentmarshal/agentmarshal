## Why

ADR-0022 section 2 adds three fields to the `review` record under schema
7: `previous_review` — the id of the task's previous review, so a task's
reviews form a chain (ADR-0016 decision 2); `classes` — a class for each
finding from the project's vocabulary, where a class outside it is
recorded as `other` rather than refused (ADR-0016 decision 3); and
`actor` inside the `reviewer` object — the declared reviewer actor the
distinct-actor rule compares (ADR-0018 decision 3). CR-154 laid down the
registry a field family declares through — field admission by schema,
validator tables keyed by record type and field, and the minimum-schema
derivation — and CR-160 and CR-173 registered families on existing
record types through it. A review today cannot say which review it
follows, how its findings class, or which declared actor judged.

## What Changes

- A review record may carry, from schema 7 only: `previous_review` — a
  record id in the form record ids take, a 26-character Crockford base32
  ULID — and `classes` — a non-empty object whose every key is a finding
  id the same record names in `findings` or `advisory_findings` and
  whose every value is a non-empty string; a class outside the project's
  vocabulary is admitted by the record, mapping it to `other` being the
  writer's — and `actor` inside the `reviewer` object, a non-empty
  string, the object staying closed to every other key.
- `previous_review` registers under the forgeable-text rule for the
  review record type and field — its ULID shape never lets the entry
  fire — and each class value and `reviewer.actor` get the same check
  inside the family's own rule, the way `accepted_pause`'s extension
  does.
- Any of the three on a review stamped below 7 is refused at write and,
  on read, under the record's own schema — the two top-level fields by
  field admission, `actor` by the reviewer object's closed keys. A
  writer carrying any of them stamps 7 through the minimum-schema
  derivation; a review carrying none is validated and stamped exactly as
  before.
- `create_review_record` accepts the three as optional keyword
  arguments.

## Capabilities

- modified: `review-evidence`

## Impact

No other record type changes, and the gate's fixtures are unchanged.
Nothing reads the fields yet: the `review` launcher that writes them,
the vocabulary mapping to `other` with a warning, and every reader —
`status`, `report --findings`, the gate's independence rules — are
later tasks.
