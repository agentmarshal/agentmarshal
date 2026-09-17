+++
schema = 2
id = "CR-103"
title = "The bound on a leak-scan rendering belongs to the caller that renders a document"
scope = [
  "src/agentmarshal/journal/capture.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/__init__.py",
  "src/agentmarshal/cli.py",
  "tests/test_capture.py",
  "tests/test_gate.py",
  "tests/test_leak_scan.py",
  "tests/test_journal.py",
  "docs/sidecar.md",
  "openspec/changes/bounded-leak-scan-output/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "every scenario in openspec/changes/bounded-leak-scan-output/specs/ is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "the standalone command prints every hit past the gate's bound, and the gate's line shows the first of them and says how many it did not show",
  "one renderer still serves both callers, and neither carries its own copy of what a hit looks like",
  "docs/sidecar.md describes the gate's warning line as the gate's own test expects it",
  "LaunchedReview can be imported from agentmarshal.journal, pinned by a test",
]
decisions = ["ADR-0005"]
documents = [
  "openspec/changes/bounded-leak-scan-output/",
  "openspec/specs/leak-scan/",
]
+++

# CR-103: the bound belongs to the caller that renders a document

## Context

CR-100 bounded the rendered leak-scan line at twenty hits for the merge
transcript's sake and shared one renderer between the gate and the standalone
command. Both deciding runs of its last round named the consequence: the bound
also applies to the command an operator runs to learn where every leak is, and
past the twentieth hit that command says "and N more not shown" with no flag
and no way to see the rest.

Three debts from the same task travel with it: the bound is nowhere in the
published capability, `docs/sidecar.md` still describes the gate's warning in
its pre-CR-100 shape, and `LaunchedReview` is missing from the journal
package's exports although the function returning it is exported.

## Objective

The bound belongs to the caller that renders into a document of its own; the
rendering stays shared.

## Acceptance Criteria

See the `acceptance` field above. The scenarios it refers to are in the delta
spec; design.md carries the decisions.

## Non-Goals

- A retention policy for what the tool leaves in the temporary directory: one
  decision for every such file, recorded as its own item, not taken here.
- A flag for the gate's bound, or a different number for it.
- Any change to what the gate refuses: the added-content scan stays advisory.
