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
  one of the candidate range's declared writer emails — the set the
  reviewer-independence check already reads — the acceptance line says
  so: ` (self-accepted: accepting party is a declared writer of the
  candidate)` after the party.
- `report` derives a completed task's `decision` from the review and the
  acceptance that apply to the `completed` record's own binding: an
  approving latest review of the completed commit reports `approved`,
  a latest acceptance carrying `findings` bound to it reports
  `accepted-over-findings`, and where that acceptance's `accepted_by`
  is a declared writer of the accepted commit the task line carries
  ` self-accepted` — the mark `status` prints — or
  ` self-acceptance-unchecked` where the commit's writers cannot be
  read.
- A journal holding no self-acceptance and no acceptance bound to an
  earlier commit prints byte-for-byte what it prints today.

## Capabilities

- modified: `operator-acceptance`

## Impact

`gate.py` computes the candidate's writer-emails set once, ahead of the
verdict block, so the acceptance line and the independence check read
the same set. `report.py` derives the decision per completed binding,
reuses the commit-writers check `status` makes for the mark —
`status_view._is_self_accepted`, called where it runs since
`status_view` imports `report` — resolving the repository through the
placement as `status` resolves it, and carries a tri-state
`self_accepted` on `TaskReport` rendered as ` self-accepted` or
` self-acceptance-unchecked` after the decision field. `status` is
untouched — it already marks.
