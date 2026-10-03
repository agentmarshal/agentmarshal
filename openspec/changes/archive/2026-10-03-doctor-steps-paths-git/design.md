## Context

CR-153 built the process log, CR-157 shipped the `step` commands that
write `step-started` and `step-ended`, and CR-162 taught `status` to
read them back: `open_steps` in `steps.py` computes a task's open
steps and their overdue spans, `step_events_by_task` groups the log's
step events under their task in one pass, and
`status_view.print_paths` prints the journal, process log and local
state paths on stderr. ADR-0014 decision 9 — as amended 2026-10-03 —
and decision 13 oblige `doctor` to do both; CR-148's review added a
third: local state resolves through `git rev-parse
--path-format=absolute`, which git older than 2.31 does not know, and
`doctor` is where a missing precondition is named.

## Goals

- `doctor` prints where everything lives — the journal, the process
  log and the local state — one line each on stderr, so the check
  report on stdout keeps its shape.
- `doctor` reports every overdue step across the project's tasks, on
  the same open/overdue computation `status` uses — a report, never a
  failure.
- `doctor`'s git check names the minimum local state needs — 2.31 —
  and fails with the remedy when the installed git is older.

## Non-Goals

- Extension checks in `doctor` (a later task).
- Stopping or signalling any process — the watchdog is a supplied
  component the harness runs.
- Steps on other machines — the log is local (ADR-0014 decision 8).
- `status`, which CR-162 already changed.

## Decisions

- **The computation and the paths printer are reused, not copied.**
  `open_steps`, `step_events_by_task` and `format_overdue` come from
  `steps.py`; `print_paths` comes from `status_view.py` — the same
  call `status` makes, so a sidecar's journal-repository paths print
  and the host's never enter the call. The process-log read is shared
  the same way: `read_process_events` in `steps.py` is the one reader
  `status` and `doctor` call — the guard that names a log it cannot
  read — the calling command's name being the only difference in the
  message it prints.
- **`run_doctor` prints the report itself.** `cli.py`'s `_run_doctor`
  prints check results and nothing else, and this change's scope does
  not reach it — so `run_doctor` gains a `stderr` keyword and a `now`
  keyword for tests, and emits the three path lines and the
  overdue-step lines there. The check list itself does not change:
  every existing check reports as before and stdout's
  `OK`/`FAIL`/`TODO` shapes are untouched.
- **An overdue-step line names its task.** `status`'s line answers
  about one task; `doctor`'s report crosses them all, so its line
  reads `Overdue step (this machine's process log): task=<id>
  step=<id> activity=<a> deadline=<iso> past=<span>`, the span in
  `step start --deadline`'s duration spelling and the whole line
  escaped like other displayed text.
- **Nothing in the report can fail the command.** A missing `log/`
  directory reads as no steps; a log that exists but cannot be read is
  named on stderr (`doctor: cannot read the process log <path>
  (<reason>)`) and reads as none; a journal whose tasks cannot be
  listed is named the same way. A local state that cannot be resolved
  marks its two lines `unavailable (<reason>)` the way `status`'s do;
  a project that cannot be found marks all three. The exit status
  stays the checks'.
- **The git check owns the version floor.** `_check_git_available`
  already runs `git --version`; it now parses the first dotted number
  — `git version 2.39.2.windows.1` reads as 2.39.2, a platform suffix
  like `.windows.1` or `(Apple Git-…)` playing no part — and compares
  it with the 2.31 local state needs for `rev-parse
  --path-format=absolute`. An older version, or one that cannot be
  read, fails the check with the minimum and the remedy — upgrade git
  — in the message; new enough reports the executable available as
  before. A version that cannot be read is judged exactly as a missing
  git: the same check fails the same way — a failed check that is no
  precondition — so the exit status is the same; only the message
  differs, carrying the minimum and the remedy.

## Risks

- [The report's stderr lines interleave with the check lines] → they
  are different streams by design: stdout keeps the check report's
  shape, stderr carries where things live and what is late.
- [A git too old for the floor can still open the repository] → the
  floor is local state's, not the repository check's: `git repository`
  may pass while `git` fails — the message says what the version is
  needed for, so the two do not read as a contradiction.
- [Patching `subprocess.run` in a test would reach other callers] →
  the version tests call `_check_git_available` directly, so the patch
  covers the one call site it means to.
