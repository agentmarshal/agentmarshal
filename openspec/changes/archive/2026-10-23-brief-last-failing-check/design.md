## Context

`build_brief` renders the implementer's briefing from the contract text
and the task's records, which `load_task_status` already loads validated
and in stored order — the record id, a ULID, so stored order is the
journal's record order. Two renderers share the file today:
`render_amendment_history` derives `## Contract amendment history` from
the records and `append_amendment_history` attaches rendered material
after prose; `_append_named_material` inlines decisions, documents and
extension material last. CR-167's `check` record — `commit`, `name`,
`result` (`passed` | `failed` | `error` | `skipped`), optional
`failed_step`, `excerpt` and `run_url` — projects to no state the brief
reads, so today it never reaches the briefing. ADR-0017 decision 3 asks
for it: the last failing `check` of the task, next to decision 2's
caveat that a check record is the observer's declaration, not proof.

## Goals

- One `## Last failing check` section naming the task's most recent
  `check` record whose `result` is `failed` or `error`: `name`,
  `result`, short `commit`, `failed_step` and `run_url` when carried,
  `excerpt` when carried — each value escaped on display.
- One sentence in the section stating the record is the observer's
  declaration, not proof.
- A sentence naming the commit when a later `check` of the same name
  passed on a different commit.
- A task with no failing check rendered byte for byte as before.

## Non-Goals

- `report` counting rejected candidates — the second half of ADR-0017
  decision 3, a later task.
- Reading the full output from the process log — the record's `excerpt`
  is what the brief carries (the change's own non-goal).
- Ordering check records by commit graph position; the record order is
  what the journal holds.
- Any change to `status`, `record-check`, the gate or the record.

## Decisions

- **A renderer beside `render_amendment_history`.**
  `render_last_failing_check(records)` returns the section text or `""`;
  `build_brief` attaches it through `append_amendment_history` — the
  separator-handling helper review already shares — after the amendment
  history and before `_append_named_material`. The record-derived
  sections stay together ahead of the inlined reference material, and a
  task with no failing check adds nothing: `""` leaves the brief byte
  for byte what it was, which a test pins.
- **Most recent means last in record order.** `task.records` arrives in
  stored order — sorted file names, `<id>-<type>.json`, so the record id
  (ULID) decides it — the same order the amendment history renders. The
  most recent failing check is the last record of `record_type` `check`
  whose `result` is `failed` or `error`; `failed` and `error` both
  count, `passed` and `skipped` do not.
- **The fix line compares record order and commits.** A `check` record
  after the failing one in record order, of the same `name`, carrying
  `result: passed` and a different `commit`, is the observer's
  declaration that the failure was later fixed; the latest such
  record's `commit` is named in short form. A pass on the same commit is
  no fix, and a pass under another name is not this check's; neither is
  named. No git is asked — the commit graph cannot order two arbitrary
  records' commits, and the record is a declaration the section already
  labels as such.
- **Fields render by their record names, escaped.** One bullet per
  field — `name`, `result`, `commit` (short form, `[:7]` as `status`
  prints it), `failed_step`, `run_url`, `excerpt` — each passed through
  `escape_for_display`, the same single escape the rest of the brief
  applies to record values. The excerpt a `record-check` writes already
  carries the forgeable characters as escapes; a record an older schema
  or a hand-written journal could still hold is escaped again here —
  escaping is idempotent, so the value can never forge a line of its
  own.
- **The caveat is one sentence of fixed text.** "A check record is the
  observer's declaration of what the pipeline found on the commit, not
  proof of it." — ADR-0017 decision 2, stated where the record's values
  are most persuasive.

## Migration

None — the change is display-side only. A journal holding no `check`
record renders the brief it always did; one holding failing checks gains
the section.

## Risks

- [A forged value reaching the section] → every field passes
  `escape_for_display` once, and a test calls the renderer with a
  newline-carrying record to pin it — the same path
  `test_brief_escapes_record_and_contract_values` exercises for the
  contract material.
- [A fix round sent after a failure already fixed] → the fix line names
  the later pass's commit, and the same-commit and other-name cases are
  tested to stay silent.
- [The brief drifting for tasks without checks] → the byte-for-byte pin
  compares the full output for a task with no check records, and a
  second pin compares the brief before and after only `passed` and
  `skipped` records land.
- [A `passed` record earlier in order being read as a fix] → only
  records after the failing one in record order are consulted.
