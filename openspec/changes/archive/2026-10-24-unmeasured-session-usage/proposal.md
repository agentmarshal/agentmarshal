## Why

An adopter's finding (digest 044, staged 2026-10-24): `record-session`
without token flags writes `0/0/0`, indistinguishable from a free run;
the only trace that nothing was measured is a missing `usage` block, and
nothing reads it that way. Adopters either record misleading zeros or
drop the session and lose its outcome. Making token counts optional on
the write side changes the record model and waits for the next record
schema; this task fixes the reading side now.

## What Changes

- A session record whose `tokens` are all zero and which carries no
  `usage` block reads as unmeasured — one definition `status` and
  `report` share. A session with a `usage` block, or with any non-zero
  token count, reads exactly as today.
- `status <task>` shows an unmeasured session's tokens as `unmeasured`
  on its record line, never as zeros.
- `report` and `report --task` leave unmeasured sessions out of every
  token sum and every cost sum and count, and print, wherever such a
  sum or count is printed — the task line, the summary line and every
  `Cost` line — how many sessions were left out as unmeasured.
- A journal holding no unmeasured session prints byte-for-byte what it
  prints today. No record is written or rewritten, and no record rule
  changes — the write side's explicit marker waits for the next record
  schema.

## Capabilities

- modified: `session-activity`

## Impact

`report.py` gains the shared unmeasured predicate, leaves such sessions
out of the token and cost sums it already builds, and names their count
on the task line, the summary line and every `Cost` line.
`status_view.py` gains a session record renderer that appends
`tokens=unmeasured` under the same predicate. `records.py`, every
writer and every record rule are untouched.
