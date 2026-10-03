+++
schema = 2
id = "CR-153"
title = "The process log: one JSON event per line, one file per writer, a reader that tolerates a torn last line and rotation"
scope = [
  "src/agentmarshal/process_log.py",
  "src/agentmarshal/localstate.py",
  "tests/",
  "openspec/changes/process-log/",
  "openspec/changes/archive/",
  "openspec/specs/process-log/",
]
acceptance = [
  "the change process-log has a proposal, a design.md and a delta spec adding the process-log capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/process-log/",
  "a writer appends events under the local state's `log/` directory (the CR-148 resolver) as one JSON object per line, `{\"format\": 1, \"at\": <UTC ISO-8601>, \"event\": <name>, \"task\"?: <id>, ...}`, to a file of its own, so that two processes writing at once never interleave or tear each other's lines; what identifies a writer's file is decided in design.md",
  "a reader returns the events of every file in order of `at`, skips an unfinished last line and a line that is not a JSON object, keeps events of kinds it does not know (as data), and reads rotated files as well as current ones; a test writes from two processes concurrently and reads every line back",
  "a file is rotated when it reaches 10 MiB and at most 5 rotated files per writer are kept, the oldest deleted first; creating `log/` goes through the local state's explicit creation call, which refuses a path outside the local state root (that call gains the containment check)",
  "the gate never imports the process-log module (a test asserts it), nothing else uses the module yet, and the full CI sequence passes",
]
documents = ["openspec/specs/process-log/"]
+++

# CR-153: the process log

## Context

ADR-0014 decisions 1, 2, 6 and 7 and ADR-0022 section 7: a local working
log, not evidence and not the journal, under the clone's local state; one
JSON object per line with the key `event`; one file per writer; a reader
that tolerates an unfinished last line and rotation; rotation, and
retention that may delete prose and prompts. The gate never reads it
(ADR-0014 decision 3). Step events, review prose, check output and
extension events are later tasks that write through this module.

## Objective

There is one place to append process events and one way to read them back.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any event producer (step commands, review prose, check output,
  extension events — later tasks) or consumer (status, doctor).
- Configurable thresholds.
- Any change to the journal.
