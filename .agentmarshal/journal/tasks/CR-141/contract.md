+++
schema = 1
id = "CR-141"
title = "ADR-0021: an acknowledged leak-scan hit"
scope = [
  "docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md",
]
acceptance = [
  "ADR-0021 renders the decision the operator approved faithfully and completely, no point dropped and none added: a separate record type, acknowledgement, and not a kind of operator acceptance (an acceptance substitutes for the approving-verdict check, and the gate's leak scan decides nothing, so there is nothing to substitute; ADR-0007's closed enumeration stays unchanged); an acknowledgement is bound to the candidate commit, names the file and the identification of the hit as the scan prints it (a signature id or a private-marker number, never the matched text) and gives a reason; nothing is hidden — the gate and the leak-scan command still print an acknowledged hit, marked with who acknowledged it and why; an acknowledged hit no longer makes the command exit 1; any declared actor may acknowledge (no roles until signing, ADR-0006); self-acknowledgement is permitted and marked as by the commit's author, as ADR-0007 decision 4 does for acceptance",
  "the ADR states, as derivations and not new decision points: the file is recorded as the scan prints it, with a path containing a private marker already masked, so the record cannot carry a marker; an acknowledgement matches a hit only on the same commit, file and identification, so a new commit or a renumbered marker list shows the hit again as unacknowledged — it fails visible, not hidden; the gate and the command find acknowledgements among the journal's records read where the gate reads records today; the gate's leak scan stays advisory and never blocks, with or without an acknowledgement",
  "the ADR names what it revises: the gate-lanes requirement that a default run is unchanged byte for byte (a run on a candidate with an acknowledged hit prints the mark), and the leak-scan scenario that the merge boundary's line carries the same detail as the command; a run with no acknowledgement prints exactly what it prints today",
  "every statement about present behaviour matches the file it rests on (the command's arguments, what it scans, its exit codes and hit line; the hit identifications; markers in project.json identified by position; the gate's advisory WARN line and the findings lane not scanning; no suppression mechanism besides the declaring file's own markers; the record types and the record file name pattern); the ADR has the form of ADR-0012..0019 including Context, Decision, Left open, Consequences and Alternatives considered, derived from the decision; the record's field names and schema number are left to the record model, a later decision without a number; it answers proposal 020's third part and links it",
  "nothing names a private document, an adopter, a client, an unpublished release or an unpublished decision by number, and the full CI sequence passes",
]
+++

# CR-141: ADR-0021 in English

## Context

Proposal 020's third part asks for an acknowledged-and-proceed path for a
leak-scan hit that is recorded rather than bypassed. The operator approved
the decision in Russian on 2026-10-03: a separate record type bound to the
commit; any declared actor; self-acknowledgement permitted and marked.

## Objective

ADR-0021 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing the record type, the gate change or the command change.
- Making a leak-scan hit block the gate (roadmap).
- The documentation map line.
