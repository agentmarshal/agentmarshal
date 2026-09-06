## Why

A review record keeps a verdict and finding ids and not one word of what the
reviewer said: 254 review records in this journal, 115 with finding ids,
zero with the prose behind them. The reviewer's output survives only as a
best-effort file under the system temp directory. Evidence that says "F-002
was found and fixed" cannot show what F-002 was. Adopter proposal 001 named
this on 0.1.0; the mechanism to fix it — hash-pinned artifacts under the
journal — exists since ADR-0009.

## What Changes

- `agentmarshal review` keeps the reviewer's full output as a file under the
  task's journal directory and pins it, by sha256, on the review record it
  writes.
- `agentmarshal submit-review` accepts a prose file and pins it the same way.
- The gate holds review artifacts to the record rule: written once, never
  modified or deleted.
- `status` and `report` show that a review carries prose.
- Nothing is required: a journal without review prose reads and gates as
  today, and a review record without `artifacts` is unchanged.

## Capabilities

### New Capabilities
- `review-evidence`: what a review record may carry beyond its verdict — the
  reviewer's prose as a pinned artifact — and how the journal keeps it.

### Modified Capabilities
<!-- none: no spec exists yet for the review record; this is the first spec in this repository -->

## Impact

`src/agentmarshal/journal/review.py` (launcher), `submit_review.py`,
`records.py` (review-record `artifacts` are already permitted on schema 2+),
`gate.py` (append-only rule over `tasks/<id>/artifacts/`), `status.py` /
`report.py` (display), `cli.py` (a `--prose` flag), docs for the two
commands. No record-schema bump: `artifacts` is an existing schema-2 field.
