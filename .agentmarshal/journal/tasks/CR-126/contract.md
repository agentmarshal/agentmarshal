+++
schema = 1
id = "CR-126"
title = "ADR-0012: what the tool does itself, and what it supplies as a compatible replacement"
scope = [
  "docs/adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md",
  "docs/README.md",
]
acceptance = [
  "ADR-0012 renders the decision the operator approved faithfully and completely: the rule for where a measured need is met; no refusal without a named replacement; declared against supplied extensions, with the supplied extension's obligations and the limit of its guarantee, and supplying distinguished from bundling; the adopter kit; core against optional, with the rule that the gate imports no optional module, checked by a test; the application to proposals 034, 035, 038 and 040 and to a living description of the system; what the core does not do; the criteria for moving an optional component into a package of its own, left open; consequences and alternatives — no point dropped and none added",
  "the ADR has the form of ADR-0011: status, date, what it builds on, a note that it records a decision and implements nothing, then Context, Decision, Left open, Consequences, Alternatives considered",
  "each proposal is referred to as 'proposal NNN', linked to its file under docs/proposals/, with its gist in a clause; earlier ADRs are named and linked; the later decisions on extensions and on where local state lives are referred to without a number; nothing names a private document, an adopter, a client or an unpublished release",
  "every statement about present behaviour or an earlier decision matches the file it rests on — ADR-0001's boundary, ADR-0010's rejections, proposal 019's disposition, what the gate compares for reviewer independence, what init creates — and the guarantee for proposal 034 is stated as declared and cross-checked against records an agent writes, not as proof",
  "the documentation map has a line for ADR-0012 in the form of the other ADR lines, and the full CI sequence passes",
]
+++

# CR-126: ADR-0012 in English

## Context

The operator approved ADR-0012 in Russian on 2026-10-02 after a discussion
that started from four measured adopter findings pressing on ADR-0001's
boundary (proposals 034, 035, 038, 040) and an adopter who left for a spec
tool. The approved text is the source; this task writes it as the project's
ADR in English. Two companion decisions — how extensions run, and where local
state lives — were approved alongside and are published after this one.

## Objective

ADR-0012 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing anything the ADR decides.
- The companion decisions' own text.
- Changing ADR-0001 or ADR-0010.
