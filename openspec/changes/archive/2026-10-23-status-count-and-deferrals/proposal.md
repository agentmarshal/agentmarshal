## Why

ADR-0016 decision 4: `status` shows the task's count of `changes_required`
verdicts — the signal to stop and revisit the contract that a person
otherwise has to notice unaided; it blocks nothing. CR-168 landed the
gate's line and CR-151 the threshold key; the `status` side of the same
decision is still missing. ADR-0016 decision 1: `status` shows the
deferrals still open — CR-175 landed `advisory_dispositions` on the
`completed` record and CR-192 the `complete` flags that write them, but
nothing shows them yet: an approval would again dissolve into silence
about defects left for later.

## What Changes

- `status <task>` prints one line with the task's count of
  `changes_required` verdicts when the count is at least one — counted
  over every review of the task's candidates exactly as the gate counts
  them since CR-168 (a review bound to a research finding is not
  counted) — naming the project's `review.changes_required_threshold`
  (default 3), marked when the count has reached it, and naming the
  threshold when it cannot be read. The line blocks nothing.
- For a task whose `completed` record carries `advisory_dispositions`,
  `status <task>` prints a `Deferrals` section listing each `deferred`
  finding with its reason and, when present, its follow-up task — and
  that task's state when the journal holds it, or that the journal does
  not hold it; `fixed` and `rejected` dispositions are counted on one
  line, not listed.
- A task with no `changes_required` verdict and no dispositions prints
  exactly today's detail view; every value the new lines take from a
  record is escaped on display.

## Capabilities

- modified: `finding-lifecycle`

## Impact

`status_view.py` gains two trailing additions inside `print_task_detail`
— the deferrals section and the count line after the agreement and drift
notices. `gate.py` is out of scope, so the count is computed in
`status_view.py` with exactly the gate's definition. The record model,
the renderer registry and every other command are unchanged; the gate's
fixtures and every documented transcript a test pins stay byte for byte.
