## Why

ADR-0014 decision 9 — as amended 2026-10-03 — and decision 13 oblige
`doctor`, like `status`, to show a step past its deadline and to print
the actual paths of the journal, the process log and the local state.
CR-162 built the machinery and did it for `status`; `doctor` still
shows neither. CR-148's review added that local state resolves through
`git rev-parse --path-format=absolute`, which git older than 2.31 does
not know — and `doctor` is where a missing precondition is named, so
its git check must name the version local state needs.

## What Changes

- `doctor` prints, once and on stderr — one line each, escaped like
  other displayed text — the actual paths of the journal, the process
  log and the local state in use, reusing `status`'s printer; in a
  sidecar the journal and the local state are the journal
  repository's. A journal or a local state that cannot be resolved
  marks its lines unavailable with the reason.
- `doctor` reports every overdue step across the project's tasks —
  one line each naming its task, on the same open/overdue computation
  `status` uses — as a report: an overdue step never makes the command
  exit non-zero, and an unreadable process log is named, not a
  failure.
- `doctor`'s git check names the minimum git version local state
  needs — 2.31, for `git rev-parse --path-format=absolute` — and
  fails, with upgrade git as the remedy in the message, when the
  installed git is older or its version cannot be read; the version is
  parsed from `git --version` output without depending on the platform
  suffix.

## Capabilities

- modified: `process-log`, `local-state`

## Impact

- `src/agentmarshal/doctor.py` and `tests/`; `cli.py` is untouched —
  `run_doctor` emits the report so the check report on stdout keeps
  its shape.
- `openspec/specs/process-log/spec.md` and
  `openspec/specs/local-state/spec.md` on archive.
