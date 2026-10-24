+++
schema = 2
id = "CR-227"
title = "0.6.0 tails, part b: the deferred stage-runner and isolation advisories of CR-223, CR-224 and CR-225"
scope = [
  "src/agentmarshal/stages.py",
  "src/agentmarshal/isolation.py",
  "src/agentmarshal/cli.py",
  "tests/",
]
acceptance = [
  "the read-only end-to-end test takes its absolute path from `AGENTMARSHAL_SNAPSHOT`, not from the working directory the re-entry under test installs (CR-223 ADV-2), and skips with the probe's reason when only the read-only guarantee is unenforced instead of silently dropping its write assertions (ADV-3); the comment above the statvfs flag mapping names `sys/statvfs.h` (ADV-4)",
  "a test shows that a `stage run` that pauses nothing never reads the journal for acceptances (CR-224: `read_records` or the loader it uses is not called), using a spy in the style already used in tests/test_stages.py",
  "`stage run` outside an initialized project prints the message it printed before CR-225 before any task-id validation (CR-225 F2), which a test pins; a failure creating a stage's temporary directory gives that stage a `not run` result line with the reason (ADR-0013 decision 7 owes every stage its line) and the run continues with the next stage, while a cleanup failure after a stage ran never replaces that stage's computed outcome; any other failure of the post-gate run after `completed` is written is caught and reported on one stderr line and never changes complete's exit status or its record (F3); tests force each case, including an OSError in complete's post-gate lane; the one-runner scenario test also runs `stage run` under the spy (F4)",
  "no requirement changes, so no OpenSpec change; no other behaviour changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = []
decisions = ["ADR-0013"]
+++

# 0.6.0 tails, part b

## Context

Advisory findings deferred to this task by their completions: CR-223
ADV-2/3/4, CR-224 `lazy-read-untested`, CR-225 F2/F3/F4 (research
`v2/backlog.md`, "Хвосты волны B").

## Objective

The deferred advisories of the stage runner and isolation are closed.

## Acceptance Criteria

As in the header.

## Non-Goals

- Documentation (a parallel task).
- Any new behaviour.
