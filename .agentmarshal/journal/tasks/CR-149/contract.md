+++
schema = 2
id = "CR-149"
title = "The status view of one task moves out of cli.py into a module with one line renderer per record type"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/status_view.py",
  "tests/",
]
acceptance = [
  "before anything moves, a test pins the full output of `agentmarshal status <task>` for a task whose records include every record type the view has a dedicated line for today and at least one type it renders with the generic line; the test passes on the code as it is",
  "the per-task view (`_print_task_detail` in cli.py and the helpers only it uses) lives in src/agentmarshal/journal/status_view.py; each record type's line is produced by a renderer looked up in one registry keyed by record type, and a type with no entry is rendered by the generic id, type and time line",
  "the output is byte-identical: the test from criterion 1 and every existing status test pass unchanged; cli.py keeps only the call",
  "no other command's behaviour or output changes, and the full CI sequence passes",
]
+++

# CR-149: the per-task status view in its own module

## Context

The 0.5.0 decisions add lines to `status <task>` for new record types and
fields (ADR-0016..0022), and ADR-0015 decision 5 makes everything it prints
escaped on display. Today the view is one function in cli.py with an
if-chain by record type; about six later tasks would edit it, and cli.py is
touched by many others. This task moves it, unchanged, so that each later
task registers a renderer.

## Objective

The per-task status view is a module with a renderer registry, and prints
exactly what it prints today.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change to what status prints, including escaping (a later task).
- The status list view (all tasks) and report.
