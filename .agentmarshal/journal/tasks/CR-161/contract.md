+++
schema = 2
id = "CR-161"
title = "The gate's transcript, the brief and the reviewer prompt escape on display what a record's text could use to forge a line"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/brief.py",
  "src/agentmarshal/journal/review.py",
  "tests/",
  "openspec/changes/escape-in-gate-brief-prompt/",
  "openspec/changes/archive/",
  "openspec/specs/record-text-safety/",
]
acceptance = [
  "the change escape-in-gate-brief-prompt has a proposal, a design.md and a delta spec modifying record-text-safety's requirement 'A refused character a record still carries is escaped on display' (MODIFIED with its exact header) so that it covers the gate's transcript, the brief and the reviewer prompt instead of calling them later work, with a scenario for each; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "every string the gate prints that comes from a record or a contract (finding ids, reasons, reviewer names, actor and source values, contract titles and the like) goes through the existing `escape_for_display`; a test gives the gate a candidate whose records carry a newline and a right-to-left override in such fields — records built in memory or with a lowered schema, as a writer around the tool could — and shows each printed escaped on its own line",
  "every such string in the brief and in the reviewer prompt (including the amendment history the prompt carries) goes through it, shown by the same kind of test for each",
  "records and contracts without such characters render byte-identically: the gate fixtures, the contract-history scenario 'a task with no amendments is unchanged' and every existing brief and review test pass unchanged",
  "the full CI sequence passes",
]
documents = ["openspec/specs/record-text-safety/"]
+++

# CR-161: escaping in the gate, the brief and the reviewer prompt

## Context

ADR-0015 decision 5: output is guarded by escaping on display, for records a
later rule does not reach at read time. CR-155 did it for status and report
and left the gate's transcript, the brief and the reviewer prompt as later
work. CR-145 made the gate check the records a candidate adds by the current
rules, but a record already in the journal — or one in a sidecar journal the
gate only advises on — is read by its own schema's rules, so a line the tool
never said could still be printed by the gate or handed to a reviewer.

## Objective

Nothing a record or contract carries can forge a line or reorder text in
the gate's output, the brief or the reviewer prompt.

## Acceptance Criteria

As in the header.

## Non-Goals

- Changing what is refused at write.
- The spec's Purpose (out of reach of the archive command; AGENTS.md).
