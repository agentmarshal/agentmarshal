## Why

ADR-0014 decision 9 — as amended 2026-10-03 — and
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 7 put the record of an in-flight step in the process log: a
`step-started` event carrying the kind of work, the process, the process's
start time and the deadline, and a `step-ended` event carrying the outcome.
CR-153 built the log and nothing writes those events yet: a harness cannot
announce a step or its deadline, so nothing can tell a step that ran past its
deadline from one still inside it.

## What Changes

- A `step` command group, registered from a new `steps.py` the way `outbox`
  registers its own — `cli.py` gets only the hook.
  `step start --task <id> --activity <a> --deadline <t> [--pid <pid>]
  [--actor <id>] [--run-dir <path>]` writes one `step-started` event and
  prints the new step id — a ULID; `step end --task <id> --step <id>
  [--outcome <word>]` writes one `step-ended` event. Neither writes the
  journal; in a sidecar both write the journal repository's process log,
  never the host's.
- The deadline is required: an ISO-8601 time or a duration such as `90m`
  measured from the command's run, recorded as a UTC ISO-8601 timestamp.
- `pid` defaults to the command's own parent process; `pid_started_at` is
  read from `/proc` on Linux and through the portable fallback `design.md`
  states elsewhere, and names itself unknown where it cannot be read rather
  than guessing.
- Two failures the CR-153 review carried: the writer refuses an event that
  cannot be encoded as strict JSON — a non-finite number or a value whose
  type JSON cannot carry — with a `ProcessLogError`, and an `OSError`
  appending reaches the caller as an error naming the log file and what to
  do, never a traceback.

## Capabilities

- modified: `process-log`

## Impact

- `src/agentmarshal/steps.py` (new), `src/agentmarshal/process_log.py`,
  `src/agentmarshal/cli.py`, `tests/`.
- `openspec/specs/process-log/spec.md` on archive.
- `status` and `doctor` reading the events and showing overdue steps is a
  later task; this change only writes them.
