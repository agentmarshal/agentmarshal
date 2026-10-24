## Why

Release audit 0.6.0, area gate-journal, findings AUD-gate-journal-5 and
-4 (confirmed by reproduction): `status` marks a self-acceptance, but
the gate's acceptance line and `report` do not, although ADR-0007
decision 4 and `docs/threat-model.md` promise the mark on every
surface. And `report` marks a task `accepted-over-findings` whenever
any acceptance carrying `findings` exists, even when the completed
commit was approved — ADR-0007 decision 5 asks `report` to
distinguish how the completed commit actually closed.

## What Changes

- Where the acceptance the gate judges carries an `accepted_by` matching
  one of the candidate range's declared writer names or emails — the
  comparison `status` makes — the acceptance line says so:
  ` (self-accepted: accepting party is a declared writer of the
  candidate)` after the party.
- `report` derives a completed task's `decision` from the review and the
  acceptance that apply to the `completed` record's own binding: an
  approving latest review of the completed commit reports `approved`,
  a latest acceptance carrying `findings` bound to it reports
  `accepted-over-findings`, and where that acceptance's `accepted_by`
  is a declared writer of the accepted commit the task line carries
  ` self-accepted` — the mark `status` prints, only where the
  self-acceptance is confirmed; `status` alone says when the check
  could not run.
- A journal holding no self-acceptance and no acceptance bound to an
  earlier commit prints byte-for-byte what it prints today.

## Capabilities

- modified: `operator-acceptance`

## Impact

`gate.py` reads the candidate range's declared writer names and emails
ahead of the verdict block, beside the emails-only set the
independence check keeps. `report.py` derives the decision per
completed binding and holds the one shared comparison —
`_accepting_party_is_declared_writer`, the check `status_view` makes —
applied by the gate over the candidate's commit range and by `report`
and `status` over the accepted commit, whose declared writers are
looked up through `status_view._declared_commit_writers` in the
repository the placement resolves, as `status` resolves it. The line
carries ` self-accepted` only where the self-acceptance is confirmed.
`status` is untouched — it already marks.
