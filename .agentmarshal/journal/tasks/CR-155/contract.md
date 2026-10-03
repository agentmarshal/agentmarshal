+++
schema = 2
id = "CR-155"
title = "status and report escape on display what a record's text could use to forge a line or reorder what is read"
scope = [
  "src/agentmarshal/journal/display.py",
  "src/agentmarshal/journal/status_view.py",
  "src/agentmarshal/journal/report.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/escape-on-display/",
  "openspec/changes/archive/",
  "openspec/specs/record-text-safety/",
]
acceptance = [
  "the change escape-on-display has a proposal, a design.md and a delta spec modifying the record-text-safety capability from refusal only to refusal at write and escaping on display (ADR-0015 decision 5), with MODIFIED requirements keeping their exact headers; every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "one function in src/agentmarshal/journal/display.py renders every character the forgeable-text rule (`forges_rendered_text` in records.py) refuses as a visible escape — `\\n`, `\\r`, `\\t` for those, `\\uXXXX` (or `\\UXXXXXXXX`) for the rest — and leaves every other character as it is; a test derives its cases from the rule's own definition, so the two cannot drift apart",
  "every string taken from a record or a contract that `agentmarshal status` prints — the task list and the per-task view — goes through it; a test gives the view records carrying a newline and a right-to-left override in free-text fields — built in memory where today's read rules would refuse them on disk, since a later rule does not reach an older schema's records (ADR-0015) — and shows each printed escaped on its one line",
  "every such string `agentmarshal report` prints goes through it, shown by the same kind of test",
  "records without such characters print byte-identically: the existing status and report tests pass unchanged, the full status pin test gains the `completed` line with a finding reference it lacked (a carried advisory), and the full CI sequence passes",
]
documents = ["openspec/specs/record-text-safety/"]
+++

# CR-155: escaping on display in status and report

## Context

ADR-0015 decision 5: rules that guard output apply by escaping on display.
A newline in a record field would print a line the tool never said; a
direction-control character would reorder what is seen. Records that a
later rule cannot reach at read time — older ones, or one written around
the writer with a lowered schema — must still not forge output. The
record-text-safety specification says "refusal" today; it becomes "refusal
at write, escaping on display". status and report come first; the gate, the
brief and the reviewer prompt are a later task.

## Objective

Nothing a record carries can forge a line or reorder text in status or
report.

## Acceptance Criteria

As in the header.

## Non-Goals

- The gate's transcript, the brief and the reviewer prompt (a later task).
- Any change to what is refused at write.
- Rewriting the `## Purpose` of the record-text-safety spec: the archive command leaves an existing spec's Purpose untouched and AGENTS.md forbids hand edits under openspec/specs/; how a Purpose is updated is a separate decision. The requirements carry the change.
