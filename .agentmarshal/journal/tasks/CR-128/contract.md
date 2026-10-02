+++
schema = 1
id = "CR-128"
title = "ADR-0013: extensions — stages, scopes, isolation, trust, switches, records"
scope = [
  "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
  "docs/adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md",
  "docs/README.md",
]
acceptance = [
  "ADR-0013 renders the decision the operator approved faithfully and completely: when an extension runs (one obligation; two stages; the rule for future stages and its candidates; the mode in the manifest; a separate step before the gate that can only pause; read from the base; no silence); isolation declared in the manifest with the pre-gate floor; where extensions live and who sees them (the extension directory, the three scopes and their tables, no footprint for a personal extension, local state outside the working tree and the executor sandbox requirement); what runs is what was approved (installation not executed by the tool, dependencies only from a lock with hashes, commands only from bin/, approval on the directory hash checked before each run, the threat model for local state); switches and the operational lane; ext records; doctor; the manifest example; left open, consequences, alternatives — no point dropped and none added",
  "the ADR has the form of ADR-0011 and ADR-0012, says it builds on ADR-0007, ADR-0010 and ADR-0012, says it partly revisits ADR-0010 and answers proposal 009, and refers to the decision on where local state lives without a number",
  "each proposal is referred to as 'proposal NNN' and linked; earlier ADRs are named and linked; nothing names a private document, an adopter, a client or an unpublished release",
  "every statement about present behaviour matches the file it rests on — where the gate runs (CI, the merge authority, inside complete after the merge), what ADR-0010's manifest declares and that the gate reads it from the base side, what an acceptance record covers under ADR-0007, that a journal-only lane exists in the gate — and ADR-0012 section 6 now names proposal 040's journal write without a shared checkout, accepted with the transactions helper, and its process-log clause reads plainly",
  "the documentation map has a line for ADR-0013 in the form of the other ADR lines, and the full CI sequence passes",
]
+++

# CR-128: ADR-0013 in English

## Context

The operator approved ADR-0013 in Russian on 2026-10-03 (fourth revision):
how extensions run, where they live, how their isolation is declared, how the
code that runs is the code that was approved, how they are switched off, and
what they may record. ADR-0012, published by CR-126, is the decision it rests
on. CR-126 landed with two review advisories on ADR-0012 carried here.

## Objective

ADR-0013 is published as the operator approved it, and ADR-0012 closes the
two points its review left.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing anything the ADR decides.
- The decision on where local state lives (its own task).
- Changing ADR-0010 or ADR-0007 text.
