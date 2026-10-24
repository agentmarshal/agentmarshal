+++
schema = 2
id = "CR-229"
title = "status and report show a session that carries no usage block and zero tokens as unmeasured, never as a zero cost"
scope = [
  "src/agentmarshal/journal/report.py",
  "src/agentmarshal/journal/status_view.py",
  "tests/",
  "openspec/changes/unmeasured-session-usage/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change unmeasured-session-usage has a proposal, a design.md and a delta spec on the capability session-activity with ADDED requirements (MODIFIED where an existing requirement states how token totals are summed — full text, heading byte for byte, every scenario); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "a session record whose `tokens` are all zero and which carries no `usage` block is read as unmeasured: `status` shows its tokens as `unmeasured` instead of zeros, and `report` leaves it out of every token and cost sum and prints, wherever such a sum is printed, how many sessions it left out as unmeasured; a session with a `usage` block, or with any non-zero token count, is read exactly as today",
  "no record is written or rewritten and no record rule changes (the write side — an explicit marker for unmeasured usage — needs the next record schema and is not this task); a journal with no such session prints exactly what it prints today, which the existing status and report tests demonstrate unchanged",
  "every value shown is escaped as today; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
decisions = ["ADR-0019", "ADR-0022"]
+++

# Unmeasured sessions read as unmeasured

## Context

An adopter's finding (digest 044, staged 2026-10-24): `record-session`
without token flags writes `0/0/0`, indistinguishable from a free run; the
only trace that nothing was measured is a missing `usage` block, and
nothing reads it that way. Adopters either record misleading zeros or drop
the session and lose its outcome. Making token counts optional on the
write side changes the record model and waits for the next record schema;
this task fixes the reading side now.

## Objective

A reader of `status` and `report` never mistakes an unmeasured session for
a free one.

## Acceptance Criteria

As in the header.

## Non-Goals

- Changing `record-session` or any record rule (next record schema).
- Rewriting existing records.
