## Context

`record-session` without token flags writes `tokens` `0/0/0` — a
session whose usage nothing measured. The zeros are indistinguishable
from a free run on read; the only trace is the missing `usage` block a
measured session carries (digest 044). `report.py` sums each task's
session tokens and costs and renders the task line, the summary and the
`Cost` lines; `status_view.py` renders each record through
`_RECORD_RENDERERS`, a session today falling back to the generic id,
type and time line.

## Goals

- A reader of `status` and `report` never mistakes an unmeasured
  session for a free one.
- One definition of unmeasured both views share.

## Non-Goals

- An explicit unmeasured marker on the record — the write side waits
  for the next record schema (the contract's non-goal).
- `record-session`, the record rules, and every other command.
- The usage provenance — an unmeasured session's usage is genuinely
  unrecorded, and `unrecorded` already says so.

## Decisions

- **Unmeasured is a read, not a field.** The predicate — a session
  record whose every token count is zero and which carries no `usage`
  key — reads the records the journal holds; nothing is written or
  rewritten. A `usage` block marks a session measured even at zero
  tokens (the zeros are a recorded measurement); a non-zero count is a
  measurement even without `usage`.
- **The predicate lives once, in `report.py`.** The session's
  measurement semantics already live there — `_usage_provenance` reads
  the same `usage` block — and `status_view.py` imports it, the way it
  already imports `status.py`'s projection. A second definition in
  `status_view.py` would drift.
- **Exclusion is silent nowhere a sum prints.** Wherever `report`
  prints a sum the omitted sessions were left out of — the task line's
  and the summary line's token sums and each `Cost` line — it appends
  `unmeasured=<n>` as the last field, only when the count is non-zero.
  A journal without unmeasured sessions prints byte-for-byte today.
- **A recorded cost sums; only an unmeasured session carrying none is
  left out.** The token sums and the `Cost` block leave different
  sessions out: a `cost` an unmeasured session recorded sums per
  currency and source exactly as a measured session's does — a sum in
  one currency is a figure the journal holds, and dropping it would
  silently lose money (ADR-0019 decision 4). Only an unmeasured session
  carrying no `cost` is left out of the `Cost` block: it counts in no
  `sessions_without_cost` — the count means sessions that ran measured
  and carried no cost — and the `unmeasured=<n>` a `Cost` line carries
  counts those sessions alone, so a task whose sessions are all
  unmeasured carrying no `cost` prints no `Cost` line.
- **`status` keeps the generic line and marks it.** The session
  renderer prints the same `- <id> session <created_at>` the fallback
  prints today and appends ` tokens=unmeasured` only under the
  predicate — a measured session's line is byte-for-byte today.
