## Why

ADR-0016 decision 1: for the review the gate passed on, `complete` takes a
disposition for each of that review's advisory findings — `fixed`;
`deferred`, with a reason, optionally naming a follow-up task; `rejected`,
with a reason — and records them in the `completed` record. ADR-0022
section 2 gives the field its shape in schema 7: `advisory_dispositions` —
`{finding id: {disposition, reason, follow_up?}}`. The findings lane's
`complete --findings` takes no dispositions. CR-154 laid down the registry
a field family declares through — field admission by schema, validator
tables keyed by record type and field, and the minimum-schema derivation —
and CR-160, CR-173 and CR-174 registered families on existing record types
through it, CR-173's a binding-dependent refusal and CR-174's an
object-valued field with per-key validation. A `completed` record today
cannot carry the recorded choice.

## What Changes

- A `completed` record bound by `completed_commit` may carry, from schema
  7 only, `advisory_dispositions` — a non-empty object whose every key is
  a non-empty finding id passing the rule finding ids pass, and whose
  every value is an object with `disposition` one of `fixed`, `deferred`,
  `rejected`; `reason`, a non-empty string, required on `deferred` and
  `rejected` and optional on `fixed`; `follow_up`, a task id in the form
  task ids take, admitted on `deferred` only; and no other key — each
  refusal naming the finding id and the key at fault.
- The same field on a record bound by `completed_finding` is refused —
  `complete --findings` takes no dispositions.
- `reason` and `follow_up` pass the forgeable-text rule — inside the
  family's own rule, the way `classes` values and `accepted_pause`'s
  `extension` do, since the table keys on top-level fields.
- The field on a `completed` record stamped below 7 is refused at write
  and on read; a writer carrying it stamps 7 through the minimum-schema
  derivation; a `completed` record without it is validated and stamped
  exactly as before.
- `create_completed_record` accepts `advisory_dispositions` as an
  optional keyword argument.

## Capabilities

- new: `finding-lifecycle`

## Impact

No other record type changes, and the gate's fixtures are unchanged.
Nothing reads the field yet: `complete --disposition` and its refusal when
an advisory finding lacks a disposition, and `status`/`report` showing
open deferrals, are later tasks.
