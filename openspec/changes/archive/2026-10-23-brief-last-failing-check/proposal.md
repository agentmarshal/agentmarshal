## Why

ADR-0017 decision 3 pairs the `check` record with visibility in the
implementer's briefing: `brief` carries the task's last failing `check`,
so the implementer of a fix round starts from what the pipeline found —
its name, its commit, the failed step, the excerpt and the run link —
not only from the reviewer's opinion. CR-167 landed the record, CR-183
the `record-check` command that writes it, and CR-184 the `status` line;
what does not exist yet is the section of the brief the decision names,
so a fix round is launched knowing the reviewer objected but not what
the pipeline refused.

## What Changes

- `agentmarshal brief --task <id>` gains one section — `## Last failing
  check` — after the amendment history and before the named material,
  naming the task's most recent `check` record whose `result` is
  `failed` or `error`: the check's `name`, its `result`, the `commit` in
  short form, `failed_step` and `run_url` when the record carries them,
  and `excerpt` when it carries one.
- The section says in one sentence that a check record is the observer's
  declaration, not proof (ADR-0017 decision 2).
- When a later `check` record of the same `name` passed on a different
  commit, the section says so, naming that commit in short form — so a
  fix round is not sent after a failure already fixed.
- Every value the section takes from the record is escaped on display as
  the rest of the brief escapes record values; a task with no failing
  `check` record yields the brief it yielded before — byte for byte.

## Capabilities

- modified: `review-evidence`

## Impact

`brief.py` gains a renderer beside `render_amendment_history`, reading
the records `load_task_status` already loads — no new journal read, no
git call, no other command touched. What a `check` record guarantees
stays what its observer declares: the section says so, and nothing in
the gate reads it.
