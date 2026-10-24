## Why

Release audit 0.6.0, area gate-journal, finding AUD-gate-journal-1
(confirmed by reproduction): the gate projects only the task it judges;
for every other task a candidate appends to it checks only for a
duplicate opening, then prints that lifecycle records are consistent. A
record the projection refuses on another task — the audit's case is a
`reopened` on a task abandoned at base — passes the gate and leaves the
journal failing `validate` after the merge. docs/threat-model.md
promises an abandoned task cannot be reopened through the gate.

## What Changes

- For every task other than the judged one to which the candidate adds
  records, the gate projects that task's merged records — the target's
  plus the candidate's — with the same lifecycle projection it applies
  to the judged task and the same closed-at-base admission rule, and
  refuses with one FAIL line naming the task and the projection's
  reason. The duplicate-opening scan this replaces is a special case of
  that projection.
- A candidate adding records its affected tasks' projections admit —
  or none — gets the transcript it gets today, byte for byte.

## Capabilities

- modified: `record-lifecycle`

## Impact

`src/agentmarshal/journal/gate.py` — the affected-tasks check inside
`run_gate`. The CR-210 WARN about another task's `opened` or
`amendment` records is unchanged.
