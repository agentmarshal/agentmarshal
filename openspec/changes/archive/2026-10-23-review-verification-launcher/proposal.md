## Why

ADR-0017 decision 4: the verdict says what the reviewer ran and with
what result, what it checked by reading only, and what it could not run
and why. Decision 5: a finding carries an optional evidence reference —
a link, a `file:line`, or the command that checked the claim with the
essential part of its output — and a finding about an external fact the
reviewer could not check is advisory, "unconfirmed". ADR-0022 section 2
names the record fields `verification` and `evidence`, and CR-178 landed
them in the record model — but nothing writes them, so a review record
still cannot say what its verdict rests on.

## What Changes

- The verdict protocol admits an optional `verification` object —
  `executed` (a list of `{what, result}`), `read` (a list of strings),
  `not_run` (a list of `{what, why}`) — and an optional `evidence`
  object mapping finding ids to the evidence behind each.
- The prompt the launcher builds asks for the `verification` sections
  and for evidence per finding id, on either binding; asks, on the
  commit binding, that the prose name each acceptance criterion's place
  in the diff and the test demonstrating it; and states that a finding
  about an external fact the reviewer could not check is advisory,
  marked "unconfirmed".
- The launcher records what the record rules admit, through the fields
  CR-178 landed: a section key outside the three, a section that is not
  a non-empty array, a malformed entry and an `evidence` entry for an id
  the verdict does not carry — or one whose value the record could not
  hold — are each dropped with a warning, never refused; the verdict is
  a paid run's output. A verdict without the sections is recorded
  exactly as before — no fields.
- `docs/quickstart.md`'s verdict-protocol section states the two keys.

## Capabilities

- modified: `review-evidence`

## Impact

The launcher's record write carries two more launch-supplied fields
through `create_review_record`; `submit-review` is untouched, as are the
gate's fixtures and every documented transcript a test pins. The pinned
reviewer prompts change — the protocol gains the two keys and the
"unconfirmed" line, and the commit prompt gains the criterion-coverage
ask. Surfacing `verification` and `evidence` in `status` and `report`,
and `submit-review` flags for them, are later tasks.
