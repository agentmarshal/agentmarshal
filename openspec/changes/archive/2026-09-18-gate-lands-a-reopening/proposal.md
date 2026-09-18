## Why

`reopen` shipped with CR-067, and its record is admitted by the projection. The
transaction that carries it cannot merge. Probed on master 2026-09-18: a task
completed at base, a candidate whose only change is the reopening record —

```
FAIL: task CR-001 is already closed at base (candidate state: open)
```

The gate decides "closed at base" by the latest lifecycle record and then admits
a closed task only a strictly additive candidate of `-session.json` files. The
projection admits a session record **or** a reopening after a terminal record;
the gate admits only the first. The existing test commits the completion and
the reopening together into the base, so it never exercised a candidate whose
diff is the reopening.

Two review runs of CR-102 named the gate's second encoding of the admitted set
as drift waiting to happen. It had already happened, and the drift is a shipped
command that cannot land.

## What Changes

The base-state check admits a candidate that only appends records the
projection admits after the task's terminal record — measurements always, a
reopening only after completion — and reads that from the projection's rule
instead of a list of file suffixes of its own.

## Capabilities

- modified: `record-lifecycle` (new requirement)

## Impact

A reopening transaction merges. Nothing that was refused before becomes
admitted except a reopening of a completed task. No record schema changes.
