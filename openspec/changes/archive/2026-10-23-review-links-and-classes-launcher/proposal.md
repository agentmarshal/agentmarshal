## Why

ADR-0016 decision 2: a review launched by the `review` command records
the previous review of the same task, so a task's reviews form a chain.
Decision 3: a finding carries a class from the project's vocabulary; a
class outside it is recorded as `other` with a warning — not refused,
because a verdict is the output of a paid run and the class is reference
markup no decision rests on. ADR-0022 section 2 names the fields
`previous_review` and `classes`: CR-174 landed them in the record model
and CR-151 the vocabulary key `review.finding_classes`. The launcher
still supplies neither.

## What Changes

- `agentmarshal review` — in its commit form and its finding-review form —
  writes `previous_review`: the id of the task's latest review record at
  launch time, whatever it bound to, read before the reviewer command
  runs so a concurrent write cannot make a review link to itself; a first
  review carries no such field. `submit-review` does not write it.
- The verdict protocol admits an optional `classes` object mapping
  finding ids to class strings, and the prompt the launcher builds lists
  the project's vocabulary — `review.finding_classes`, the default when
  unset — and asks for one class per finding id.
- The launcher records `classes` entries for ids among the verdict's
  `findings` or `advisory_findings`: a class outside the vocabulary is
  recorded as `other` with a warning naming the id and the class given;
  an entry for an id the verdict does not carry is dropped with a
  warning; a `classes` that is not an object or holds a non-string value
  is dropped as a whole with a warning. The verdict is never refused over
  a class.
- A verdict without `classes` is recorded exactly as before — no
  `classes` field, the schema stamp rising only for `previous_review`.

## Capabilities

- modified: `review-evidence`

## Impact

The launcher's record write moves beside it: `submit_review`'s signature
is the human path's and gains nothing, so `journal/review.py` writes the
launched record itself — the same load-check-record-write sequence —
with the two fields only a launch can supply. No other command changes;
the gate's fixtures are unchanged. Surfacing the fields in `status` and
`report`, and the mode that shows the reviewer the previous round's
findings, are later tasks.
