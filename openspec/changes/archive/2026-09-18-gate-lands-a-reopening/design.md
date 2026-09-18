## Context

`run_gate` computes `closed_at_base` from the latest of the task's
`-completed.json`/`-abandoned.json`/`-reopened.json` files in the base tree, and
then admits a closed task only when `measurements_only` holds: every change is an
addition inside the task's own journal subtree and every added record is a
`-session.json`. CR-102 put the projection's rule in one place in `status.py`
(`_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, plus the "reopen only from done"
predicate in `load_task_for_record`). The gate never read it.

## Goals

- A reopening of a completed task lands through the gate.
- The gate and the projection agree on what a closed task admits, from one rule.

## Non-Goals

- Changing what the projection admits.
- Changing the other strictness of the lane: every change must still be an
  addition inside the task's own subtree. A reopening transaction that also
  edits a file stays refused.
- The sidecar placement, where the gate already asks the journal's projection.

## Decisions

- **The gate asks the projection's rule, keyed by record type.** The added
  records' types come from their file names (the gate reads no record content
  in this check, and must not start), mapped to the projection's record types;
  what is admitted comes from `status.py`. One rule, read twice, instead of two
  rules that already disagreed.
- **The terminal state matters.** A reopening is admitted only when the latest
  lifecycle record at base is a completion. The gate already knows which record
  that is — it sorts them — so the distinction costs a name comparison.
- **The transcript line names what was admitted.** The existing PASS line says
  "measurements-only append"; a reopening gets a line that says so, so a
  transcript does not describe a reopening as a measurement.

## Risks

- [A candidate reopens and does work in the same transaction] → still refused:
  the lane stays strictly additive inside the task's subtree, and work is a
  diff outside it. Reopening and working are two transactions, as they are for
  a person.
- [The byte-for-byte transcript tests] → they exercise open tasks; the
  measurements line is pinned by its own test and does not change.
