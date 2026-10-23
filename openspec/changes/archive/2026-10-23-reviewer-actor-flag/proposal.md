## Why

ADR-0018 decision 3 lets a contract name its permitted reviewers and an
independence rule `distinct-actor`; ADR-0022 section 2 puts the declared
reviewer actor on the review record as `reviewer.actor` for the gate to
compare. CR-174 landed the key in the record model and
`create_review_record` accepts it, but neither command that writes a
review can set it — every review lacks it, and the gate checks that
follow (membership in `reviewers`, `distinct-actor`) would have nothing
to read.

## What Changes

- `agentmarshal submit-review` and `agentmarshal review` — the launcher
  in its commit form and its finding-review form — take an optional
  `--actor <id>`; given, the review record's `reviewer` object carries
  `actor` with that value through `create_review_record`'s
  `reviewer_actor` parameter, and the record stamps schema 7 by the
  minimum-schema derivation.
- A value the record rules refuse — empty, all whitespace, or a
  character that could forge a line — is refused before anything is
  written and, for the launcher, before the reviewer command starts:
  a launched reviewer costs a paid run. The refusal names `--actor`.
- An id the project's actors table does not declare is accepted and
  recorded as given, and the command notes it is not a declared actor —
  actors are declared, never authenticated (ADR-0006).
- `review --dry-run --actor` is admitted — the one record flag a dry run
  accepts — and shows the actor a recorded review would carry.
- Without `--actor` the record, its schema stamp and every line the
  commands print are exactly as before; `recorded_by` — who wrote the
  record — and `reviewer.actor` — who is said to have reviewed — stay
  independent.

## Capabilities

- modified: `review-evidence`

## Impact

Only the two review-writing commands change; no other command changes
and the gate's fixtures are untouched. The gate checks that read the
actor — membership in a contract's `reviewers`, the `distinct-actor`
rule — and `status` showing it are later tasks.
