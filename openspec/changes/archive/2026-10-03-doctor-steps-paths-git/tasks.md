## 1. The git version

- [x] 1.1 `doctor.py`'s git check parses the first dotted number of
  `git --version` — a platform suffix playing no part — and fails,
  naming 2.31 as the minimum local state needs for `git rev-parse
  --path-format=absolute` and upgrade git as the remedy, when the
  installed git is older or the version cannot be read — verify: tests
  patching the reported version both ways, plus the boundary and the
  suffix case.

## 2. The paths and the steps

- [x] 2.1 `run_doctor` prints the three paths on stderr — `journal:`,
  `process log:` and `local state:`, one line each and escaped,
  reusing `status_view.print_paths`; a project that cannot be found
  marks all three unavailable, a local state that cannot be resolved
  marks its two — verify: the tests of the line shapes, the escape and
  the sidecar case included.
- [x] 2.2 `run_doctor` reports every overdue step across the project's
  tasks — `list_task_statuses` plus `open_steps` over the task's own
  slice, the log read once per run — each line naming its task and
  this machine's process log; an overdue step never fails the command
  and an unreadable log is named, not a failure — verify: the
  command-level tests.

## 3. The change itself

- [x] 3.1 `openspec/changes/doctor-steps-paths-git/` carries proposal,
  design and the process-log and local-state deltas — verify:
  `openspec validate` (or `status`) reads it clean and the archive
  lands it under `openspec/changes/archive/` with
  `openspec/specs/process-log/` and `openspec/specs/local-state/`
  updated by the archive command.
