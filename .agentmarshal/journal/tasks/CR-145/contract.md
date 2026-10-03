+++
schema = 2
id = "CR-145"
title = "A record is read by its own schema's rules and written by the current ones; writers stamp the minimum schema from a table"
scope = [
  "src/agentmarshal/journal/records.py",
  "tests/",
  "openspec/changes/read-rules-by-schema/",
  "openspec/changes/archive/",
  "openspec/specs/record-schema/",
]
acceptance = [
  "the change read-rules-by-schema has a proposal, a design.md and a delta spec adding the record-schema capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the implementation follows design.md or records there why it departed; the change is archived with the archive command into openspec/specs/record-schema/",
  "records.py holds one table mapping every read-time rule — each check that record validation makes on a record type, a field or a field's value — to the schema it applies from; every rule that exists today applies from schema 1 except the field gates already bound to schemas 2, 4, 5 and 6, which keep their numbers; a test fails when a rule is checked without an entry in the table (design.md says how the test finds the rules)",
  "validation splits by side, as ADR-0015 decision 1 says: the write path (validate_record_for_write) applies every current rule whatever schema the record carries; the read paths (read_records, and validate_record_content, which the gate uses on added records) apply only the rules of the record's own schema and below; a test with a rule registered from a schema one above the highest supported shows a record of the highest schema accepted on read and refused on write, and the test-only rule never reaches production code",
  "every writer stamps the minimum schema derived from the fields the record carries — each create_* function and session_record_schema use one derivation instead of hand-written choices; a parametrized test pins that each writer stamps, for the same input, exactly the number it stamps today (3, 4, 5 and 6 where they occur)",
  "no existing behaviour changes: `uv run agentmarshal validate` passes on this repository's journal, no existing test is weakened, and the full CI sequence passes",
]
documents = ["openspec/specs/record-schema/"]
+++

# CR-145: read rules by schema, minimum schema from a table

## Context

ADR-0015 decided that a record is checked at write time by the current
rules and at read time by the rules of its own schema, that writers stamp the
minimum schema, and that a table "rule → the schema it applies from" lives in
record validation with a test that catches a rule without its number.
Today records.py has one validation function used on every path, and each
writer chooses its schema number by hand. ADR-0022 will add schema 7; this
task lays the ground so that later tasks only register their fields and
rules.

## Objective

Record validation knows, per rule, the schema it applies from, and applies
it on the side ADR-0015 says; writers derive their schema number.

## Acceptance Criteria

As in the header.

## Non-Goals

- Schema 7 or any new field or record type (later tasks).
- Escaping on display (ADR-0015 decision 5; a later task).
- The contract header and the extension manifest (their own tasks).
- Any change to which records are accepted or refused today.
