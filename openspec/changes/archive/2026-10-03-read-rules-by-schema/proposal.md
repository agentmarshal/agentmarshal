## Why

ADR-0015 decided that a record is checked at write time by the current rules
and at read time by the rules of its own schema, that writers stamp the
minimum schema a record needs, and that a table "rule → the schema it applies
from" lives in record validation with a test that catches a rule without its
number. Today `records.py` has one validation function used on every path,
and each writer chooses its schema number by hand, so neither half of the
decision is in the code. ADR-0022 will add schema 7; laying the table down
now means the later tasks only register their fields and rules.

## What Changes

Record validation becomes an ordered registry of named read-time rules plus
one table `_RULE_FROM_SCHEMA` binding each rule to the schema it applies
from. Every rule that exists today is bound to schema 1, except the field
gates already bound to schemas 2, 4, 5 and 6 — provenance, finding bindings,
`reviewed_contract`, and the coordination activity — which keep their
numbers. Validation splits by side (ADR-0015 decision 1):
`validate_record_for_write` applies every rule whatever schema the record
carries, while `read_records` and `validate_record_content` apply only the
rules of the record's own schema and below.

Every `create_*` writer and `session_record_schema` stamp the minimum schema
through one derivation over the record's fields and values instead of
hand-written choices. For the inputs each writer produces today the stamped
number is unchanged (3, 4, 5 and 6 where they occur now).

## Capabilities

- added: `record-schema`

## Impact

A rule bound to a later schema can no longer refuse history on read, which is
what halts an upgrade over journals like the one in proposal 025. Nothing
changes about which records are accepted or refused today: writers stamp the
same numbers, the write path checks the same set of rules, and every lawful
record reads under the rules that governed it already. The next schema's
task registers a field family, its gates and its rules in a few lines each.
