+++
schema = 2
id = "CR-164"
title = "The gate escapes candidate paths and the values in its error messages, so a file name cannot forge a line of its output"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/escape-gate-paths-and-errors/",
  "openspec/changes/archive/",
  "openspec/specs/record-text-safety/",
  "openspec/specs/scope-enforcement/",
]
acceptance = [
  "the change escape-gate-paths-and-errors has a proposal, a design.md and a delta spec: record-text-safety gains a requirement that the gate's transcript escapes every value it did not write itself — candidate paths, rename sources and targets, and values carried into error and refusal messages — and scope-enforcement's path-naming requirement is MODIFIED (exact header) to say paths are named in escaped form; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "every path the gate prints — paths outside the contract's scope, rename sources and targets, record paths, extension and manifest paths — goes through `escape_for_display`; a test commits a file whose name carries a newline and one whose name carries a right-to-left override and shows each named escaped on its own line, with `gate: passed` printed nowhere it was not",
  "every gate error or refusal message that embeds a value from the candidate, the journal or git output (an exception text, a ref, a path) escapes that value; a test drives at least one such message with a forgeable value",
  "a candidate whose paths and values carry no refused character produces byte-identical output: the gate fixtures and every existing gate test pass unchanged",
  "the full CI sequence passes",
]
documents = ["openspec/specs/record-text-safety/", "openspec/specs/scope-enforcement/"]
+++

# CR-164: escaping paths and error values in the gate

## Context

CR-155 and CR-161 escape on display every value taken from a record or a
contract. A candidate's file names are neither, and the gate prints them
as they are — a file named with a newline could print a line the gate never
said (`gate: passed`). The CR-161 review also found gate error messages that
carry values unescaped. Git itself quotes unusual names unless told not to;
the gate reads paths raw (`-z`), so the escaping is the tool's job.

## Objective

Nothing a candidate controls can forge a line or reorder text in the gate's
output.

## Acceptance Criteria

As in the header.

## Non-Goals

- Refusing such file names (they are legal in git; naming them escaped is enough).
- Output of commands other than the gate.
