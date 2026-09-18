## Why

The projection has always refused to read a task whose records carry work after
a terminal record. The writer never refused to write one.

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
writer without a guard. `accept`, `amend`, `finding` and `complete` already
refused through five private copies of the rule and now refuse through the one
in the projection's module. `review` refuses before it starts the reviewer,
which is new for both bindings. `record-session` keeps working on a closed
task, and `reopen` keeps its own refusal for an abandoned one, which the guard
now mirrors. No record schema changes.
