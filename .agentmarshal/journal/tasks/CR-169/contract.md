+++
schema = 2
id = "CR-169"
title = "At capture level hash the reviewer's prose and diagnostics are kept under the clone's local state and announced in the process log"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/process_log.py",
  "tests/",
  "openspec/changes/review-prose-to-process-log/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
  "openspec/specs/reviewer-adapter/",
]
acceptance = [
  "the change review-prose-to-process-log has a proposal, a design.md and deltas: review-evidence's requirement 'The capture policy decides where a review's prose goes' is MODIFIED (exact header) so that at `hash` the prose is kept under the clone's local state instead of a temporary file, and reviewer-adapter's 'The reviewer command's diagnostics survive a successful run' is MODIFIED likewise for diagnostics; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "at capture level `hash`, the accepted verdict's output is written byte for byte to a file under the local state's process-log area (the layout is stated in design.md), and a `review-prose` event carrying the task, the file's path and its sha256 is appended to the process log; stderr names the path as today; the journal holds nothing — no artifact, no field",
  "whatever the reviewer command wrote to its error stream on a successful run is written the same way and announced by a `review-diagnostics` event, at every capture level",
  "when local state cannot be used (git cannot name it, the directory cannot be created), the output falls back to a temporary file as today, and stderr says why; levels `commit` and `off`, and the rejected-verdict copy, behave exactly as before",
  "in a sidecar the files and events go to the journal repository's local state, never the host's; the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/", "openspec/specs/reviewer-adapter/"]
+++

# CR-169: review prose and diagnostics in the process log

## Context

ADR-0014 decisions 1 and 11: the process log holds review prose at capture
level `hash` (the journal keeps the hash, not the prose) and reviewer
diagnostics at any level; ADR-0022 section 7 names the `review-prose` event
(path and sha256) and `review-diagnostics`. Today the launcher keeps both
in a temporary file, because the private store did not exist; CR-148 and
CR-153 built the local state and the log.

## Objective

A review's prose and diagnostics are kept where the clone keeps its
working state, and the log says where.

## Acceptance Criteria

As in the header.

## Non-Goals

- Retention beyond the log's existing bound (CR-153).
- Any change at levels `commit` or `off`.
- Reading the prose back in any command.
