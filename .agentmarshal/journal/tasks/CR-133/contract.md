+++
schema = 1
id = "CR-133"
title = "ADR-0015: a rule applies from the schema that introduced it"
scope = [
  "docs/adr/ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md",
]
acceptance = [
  "ADR-0015 renders the decision the operator approved (third revision) faithfully and completely: checks at write time by the current rules whatever schema the writer stamps; checks at read time by the record's own schema; the minimum schema kept; tightening at read time only with a new schema and loosening for all; no existing record refused by a later rule; output-guarding rules applied by escaping on display, in every place the approved text lists; existing checks from schema 1 and why; the rule-to-schema table and its test; the same rule for the contract header and the extension manifest; consequences and alternatives — no point dropped and none added",
  "the ADR has the form of ADR-0011..0013, builds on ADR-0004, ADR-0011 and ADR-0013, names its revision of the record-text-safety specification (refusal at the boundary only, becoming refusal at write and escaping on display), and answers proposal 025's second suggestion",
  "every statement about present behaviour matches the file it rests on — the minimum-schema rule (ADR-0004, ADR-0011, records.py), strict reading (ADR-0004), what 0.4.0 and 0.4.1 did to the forgeable-text rule (CHANGELOG, proposal 025), the separate schema numbers of the contract header and the manifest",
  "proposals are referred to as 'proposal NNN' and linked; ADRs are named and linked; the release check against adopters' journals is not mentioned; nothing names a private document, an adopter, a client or an unpublished release or decision by number",
  "the full CI sequence passes",
]
+++

# CR-133: ADR-0015 in English

## Context

0.4.0 tightened the forgeable-text rule and refused records that 0.1.0 had
written lawfully, in tasks long closed (proposal 025); 0.4.1 narrowed the rule
but not the cause. The operator approved ADR-0015 in Russian (third revision,
2026-10-03) after a cross-check showed writers stamp the minimum schema a
record needs, so the rule splits into write time and read time.

## Objective

ADR-0015 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing the table, the escaping, or the specification change.
- The documentation map line (added by the next ADR task).
