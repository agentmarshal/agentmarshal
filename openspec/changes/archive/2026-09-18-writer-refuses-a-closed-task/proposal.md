## Why

The projection has always refused to read a task whose records carry work after
a terminal record. The `submit-review` writer never refused to write one.

Probed on a throwaway journal while CR-101 argued about a pre-run refusal:

```
agentmarshal open …            -> ok
agentmarshal abandon …         -> ok, terminal record
agentmarshal submit-review …   -> exit 0, the review record lands
agentmarshal status CR-001     -> FAIL: task has a lifecycle record after a terminal record
agentmarshal validate          -> journal invalid
```

One ordinary command, reachable by a person today, leaves the task unreadable
and the journal invalid — and an append-only journal cannot take the record
back. The rule lives in the reader; the writer has to hold it too.

## What Changes

Every command that writes a record into an existing task asks the projection
whether the task still admits one, and refuses when it does not, naming the
state. The two records the projection admits after a terminal record — a
measurement and a reopening — keep working, because the cost accounting of a
completed task depends on the first and recovery depends on the second.

A launched review refuses a closed task before it starts the reviewer, so
discovering the refusal costs no paid run.

## Capabilities

- new: `record-lifecycle`

## Impact

`submit-review` refuses a closed task instead of corrupting it — it was the
writer without a guard. Eight paths already had private `state != "open"`
refusals: `accept`, `amend`, `finding`, the three completion paths, sidecar
`complete`, and finding review. Commit review gains its pre-run refusal here;
finding review had one since CR-101. `record-session` keeps working on a closed
task, and `reopen`'s own `state != "done"` refusal moves into the guard. No
record schema changes.
