## Why

ADR-0017 decision 4: the verdict says what was executed and what was
read — what the reviewer ran and with what result, what it checked by
reading only, and what it could not run and why. Decision 5: a finding
carries an optional evidence reference — a link, a `file:line`, or the
command that checked the claim with the essential part of its output.
ADR-0022 section 2 names the fields `verification` and `evidence` on the
`review` record in schema 7, and CR-174 laid down how the review field
family registers — the field family, the shared validator tables, the
family's own schema-bound rule and the minimum-schema derivation. A
review today cannot say what its reviewer executed nor cite the evidence
behind a finding.

## What Changes

- A review record may carry, from schema 7 only: `verification` — an
  object with one or more of the keys `executed`, `read` and `not_run`
  and no other key, `executed` a non-empty array of objects carrying
  exactly `what` and `result`, `read` a non-empty array of strings, and
  `not_run` a non-empty array of objects carrying exactly `what` and
  `why`, every string inside non-empty and passing the forgeable-text
  rule — and `evidence` — a non-empty object whose every key is a
  finding id the same record names in `findings` or `advisory_findings`
  and whose every value is a non-empty string passing the same rule.
- Neither field registers in the forgeable-text table — both are
  objects, and a table entry would fail-closed on the dict — so every
  string inside takes the same `_reject_control_characters` check inside
  the family's own rule, the way `classes`' values and `reviewer.actor`
  do; `evidence` keys bind by the one named-finding check `classes` uses.
- Either field on a review stamped below 7 is refused at write and, on
  read, under the record's own schema; a writer carrying either stamps 7
  through the minimum-schema derivation; a review carrying neither is
  validated and stamped exactly as before.
- `create_review_record` accepts the two as optional keyword arguments.

## Capabilities

- modified: `review-evidence`

## Impact

No other record type changes, and the gate's fixtures are unchanged.
Nothing reads or writes the fields yet: the review protocol lines that
ask the reviewer for the sections, the launcher writing them, the
"unconfirmed" advisory line, and every reader are later tasks — as are
`mode: resolution` and `carried_approval`, blocked pending the review of
the queue model.
