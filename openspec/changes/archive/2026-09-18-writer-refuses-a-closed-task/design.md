## Context

`project_status` (status.py) raises "task has a lifecycle record after a
terminal record" for any record other than `session` or `reopened` once a
terminal record is present. Writers call `load_task_status` first — which
succeeds, because the journal is still valid at that moment — and then append.
The next read of that task fails, and `validate` reports the whole journal
invalid.

Writers today: `submit_review.py`, `acceptance.py`, `session.py`,
`complete.py`, `open_task.py`, and two paths straight out of `cli.py`
(`amend`, `finding`). The state of them before this change, checked against the
diff rather than assumed: `submit_review` loaded the projection and ignored
what it said — that is the hole the probe fell through. `acceptance`,
`complete` (three paths), and the CLI's `amend` and `finding` each carried
their **own** `state != "open"` refusal, in five different spellings. `session`
must admit a closed task and does. `open_task` allocates a new identifier and
has no existing task to write into.

So the defect was one writer without a guard, beside five writers each holding
a private copy of the same rule — which is the other half of the problem: five
copies drift, and one of them already had.

## Goals

- One rule, one home, every writer.
- The refusal says which state the task is in.
- `record-session` after completion keeps working (am-land records cost there).

## Non-Goals

- Changing what the projection admits. The reader's rule is the rule; this
  change makes the writer obey it.
- Repairing journals already corrupted this way: nothing in this release can
  remove a record, and a repair path is a separate decision.
- A new record type, a new field, or a schema bump.

## Decisions

- **The guard belongs to the module that owns the projection.** `status.py`
  gains a helper that loads the task and refuses when the state is terminal for
  the record about to be written; every writer calls that instead of
  `load_task_status`. Putting the check in `write_record` was the alternative
  and was rejected: that function takes a record and a path and knows nothing
  about a task's history, and giving it that knowledge would make every caller
  pay for a projection it may already hold.
- **The admitted set is named once, from the projection's own constant.** The
  writer must not carry a second list of "records allowed after a terminal
  record" — that is the drift CR-100 and CR-101 both paid for. The helper reads
  the same set the projection uses.
- **The launcher refuses before it pays.** A review of a closed task would be a
  spent reviewer run and then a refused write. CR-101 settled this shape for a
  finding review; a commit review gets it for the same reason.

## Risks

- [A guard in the writer breaks am-land's cost step] → `session` is admitted
  after a terminal record by the projection, and the helper asks the projection;
  a test pins that `record-session` after `complete` still works.
- [Existing journals with a work record after completion cannot be read] → they
  already cannot; this change stops new ones appearing and says so in Non-Goals
  rather than pretending to repair.
