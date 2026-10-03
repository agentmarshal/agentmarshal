+++
schema = 2
id = "CR-157"
title = "agentmarshal step start and step end record a step's start, deadline and end in the process log"
scope = [
  "src/agentmarshal/steps.py",
  "src/agentmarshal/process_log.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/step-commands/",
  "openspec/changes/archive/",
  "openspec/specs/process-log/",
]
acceptance = [
  "the change step-commands has a proposal, a design.md and a delta spec modifying the process-log capability (MODIFIED requirements keep their exact headers, ADDED for new ones); every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal step start --task <id> --activity <a> --deadline <time> [--pid <pid>] [--actor <id>] [--run-dir <path>]` validates the task id, takes the activity from the session activity vocabulary, requires a deadline (an ISO-8601 time or a duration such as `90m`, stated in design.md), writes one `step-started` event (step id, activity, pid, pid_started_at, deadline, and actor and run_dir when given) and prints the step id; without `--pid` it records its own parent process",
  "`pid_started_at` is the process's start time read from the platform where it can be read (Linux `/proc`, and a portable fallback stated in design.md); where it cannot, the field says so rather than guessing, and the command still works",
  "`agentmarshal step end --task <id> --step <id> [--outcome <word>]` writes one `step-ended` event; an outcome must be a non-empty word without forgeable characters; neither command writes anything to the journal, and in a sidecar both write the journal repository's process log, never the host",
  "the process-log writer refuses an event that cannot be encoded as strict JSON (NaN, infinity, an unsupported type) with a clear error, and an OSError while appending reaches the caller as an error naming the log file and what to do, never a traceback (carried from the CR-153 review); cli.py keeps only the hook, and the full CI sequence passes",
]
documents = ["openspec/specs/process-log/"]
+++

# CR-157: step start and step end

## Context

ADR-0022 section 7 and the operator's decision on the step form
(2026-10-03): the core records step events — a step started with its kind of
work, process, process start time and deadline, and a step ended with its
outcome — in the process log; the watchdog and monitor are a supplied
component the harness runs; the core starts no background process. `step
end` is an optional addition: a step is still closed by the record it ends
with. CR-153 built the log. Showing overdue steps in status and doctor is a
later task.

## Objective

A harness can announce a step and its deadline in one command, and close it
in another.

## Acceptance Criteria

As in the header.

## Non-Goals

- Showing steps in status or doctor (a later task).
- Any watchdog, heartbeat or process control.
- Writing the journal.
