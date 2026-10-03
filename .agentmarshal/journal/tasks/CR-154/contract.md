+++
schema = 2
id = "CR-154"
title = "Record schema 7 is known, record types come from one registry, and the shared limits for 0.5.0's new fields exist"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/status.py",
  "tests/",
  "openspec/changes/record-schema-7/",
  "openspec/changes/archive/",
  "openspec/specs/record-schema/",
]
acceptance = [
  "the change record-schema-7 has a proposal, a design.md and a delta spec modifying the record-schema capability (MODIFIED requirements keep their exact headers); every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "schema 7 is a supported record schema: a record of schema 7 that carries only fields older schemas allow is written and read; schema 8 is unknown and refused (the existing test that uses 7 as the unknown example moves to 8); no writer stamps 7 yet, because no field requires it",
  "the record types are declared once: one registry gives, per type, its predicate type, the state it projects, whether it is admitted after a terminal record, whether it is writable, and whether `recorded_by` with `recorded_by_source` is required; PREDICATE_TYPES in attestation.py, the state table, the after-terminal set and the writable types in status.py are derived from it, or a test pins them equal to it; `finding` moves onto the recorded-by flag with no change in behaviour",
  "shared validators exist for what 0.5.0's new fields need — text bounded by a number of characters, JSON bounded by a number of bytes after canonical encoding, and the forgeable-text rule — each registered in the rule table as its own entry applying from schema 7 (never folded into an existing schema-1 group), and exercised by tests through a test-only field; no production field uses them yet",
  "nothing that schemas 1 to 6 accept or refuse changes, the gate's fixtures are unchanged, `uv run agentmarshal validate` passes on this repository's journal, and the full CI sequence passes",
]
documents = ["openspec/specs/record-schema/"]
+++

# CR-154: record schema 7 and one registry of record types

## Context

ADR-0022 brings 0.5.0's new fields and record types under one record schema,
7. CR-145 gave record validation a rule table by schema and a derived
minimum schema. Before any field family arrives, schema 7 must be known,
the record types must be declared in one place (they are listed in three
today: records, attestation, status), and the limits the new fields share
(ADR-0022 section 8: an excerpt of 4 KiB, a payload of 64 KiB, a reason of
1000 characters, the forgeable-text rule) must exist as rules of schema 7.

## Objective

Each later task adds its fields or record type by registering it, nothing
more.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any new field or record type (later tasks, one family each).
- Writing schema 7 from any writer (the contract-hash task does that).
- Escaping on display.
