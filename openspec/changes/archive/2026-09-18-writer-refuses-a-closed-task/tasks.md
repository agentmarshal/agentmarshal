## 1. The guard

- [x] 1.1 `status.py` exposes one helper that loads a task and refuses when its projected state is terminal for the record type about to be written, reading the admitted set from the projection's own constant — verify: no second list of admitted types exists in the tree (grep).
- [x] 1.2 The refusal names the state the task is in — verify: test on a completed and an abandoned task.

## 2. Every writer

- [x] 2.1 `submit-review` refuses a closed task and writes nothing — verify: test per terminal state, asserting the record count is unchanged and `validate` still passes.
- [x] 2.2 `accept`, `amend` and `finding` refuse a closed task and write nothing — verify: one test each.
- [x] 2.3 `complete` and `abandon` refuse a task that is already closed — verify: one test each.
- [x] 2.4 `record-session` after completion still works, and `reopen` still works — verify: one test each.

## 3. Before the run

- [x] 3.1 `review` refuses a closed task before starting the configured reviewer, for both bindings — verify: launcher tests asserting no reviewer process ran and no prompt file was written.
