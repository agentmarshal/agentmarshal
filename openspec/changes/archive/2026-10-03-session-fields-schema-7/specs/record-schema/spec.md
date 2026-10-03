## MODIFIED Requirements

### Requirement: Every read-time rule is bound to the schema it applies from in one table
Record validation SHALL hold a table mapping every read-time rule — each
check it makes on a record type, a field, or a field's value — to the schema
the rule applies from. Every rule that existed before schema 7 applies from
schema 1 except the field gates already bound to schemas 2, 4, 5 and 6,
which keep their numbers: provenance from 2, the finding record and finding
bindings from 4, `reviewed_contract` from 5, the coordination activity
from 6. The shared field validators the schema-7 field families need — a
text bounded by a number of characters, a text bounded by a number of
UTF-8-encoded bytes, a JSON value bounded by a number of bytes after
canonical encoding, and the forgeable-text rule — SHALL each be a table
entry of their own, bound to schema 7, and SHALL NOT be folded into a rule
bound to an earlier schema: a tightening hidden inside a schema-1 rule
would apply to old records. A shape rule a field family adds for its own
fields — a form no shared validator covers, as the session family's
`commit` hex shape and non-empty strings are — SHALL likewise be a table
entry of its own, bound to the schema the family registers under, for the
same reason. A rule SHALL NOT be checked without an
entry in the table, and a read path SHALL apply no rule whose entry is
missing. The schema-version check is a precondition of the table itself —
it is what makes the record's number known — so it runs ahead of every rule
and holds no entry. Some rules compare a record with where it lies: `task`
against the task the record is written to or read from, `record_type`
against the file name that carries it, a finding binding against the
findings the task holds. Such a rule SHALL be bound in the table like any
other and SHALL apply where the path supplies that placement — the read
path supplies the directory and the file name; the write side supplies the
destination and, where the task's findings are at hand, the finding set. A
rule whose placement a path does not supply SHALL NOT be applied there.

#### Scenario: a rule cannot be checked without an entry in the table
- **WHEN** a check is registered as a rule without a table entry
- **THEN** the completeness check fails, and no read path applies the rule

#### Scenario: a rule comparing a record with where it lies applies where the path supplies that placement
- **WHEN** a record bound to a finding the task does not hold is read from
  the journal
- **THEN** it is read under its own schema's rules — the task's findings
  are the write side's placement — while the same record presented for
  write is refused

#### Scenario: today's rules apply from schema 1 except the gates bound to 2, 4, 5 and 6
- **WHEN** the table's bindings are read
- **THEN** every rule is bound to schema 1 except provenance (2), the
  finding record and its bindings (4), `reviewed_contract` (5), the
  coordination activity (6), the shared field validators (7) and the
  schema-7 field families' own shape rules (7)

#### Scenario: the shared validators are entries of their own bound to 7
- **WHEN** the table's entries for the bounded-text, bounded-text-bytes,
  bounded-JSON and forgeable-text rules are read
- **THEN** each is bound to schema 7, and none is folded into a rule bound
  to an earlier schema

### Requirement: A writer stamps the minimum schema the record needs
Every writer SHALL stamp the least schema that admits the fields and values
its record carries, derived by one derivation over the record rather than a
hand-chosen number. The base record model stamps 3; a finding record or a
record bound to a finding stamps 4; `reviewed_contract` stamps 5; a
coordination activity stamps 6; a field a schema-7 family admits stamps 7 —
exactly the numbers the writers stamp today.

#### Scenario: each writer stamps the minimum schema its record needs
- **WHEN** a `create_*` function or `session_record_schema` builds a record
- **THEN** the stamped schema is 3 for the base model and exactly 4, 5, 6
  or 7 where the record's own fields and values require them

### Requirement: Schema 7 is a supported record schema
Record validation SHALL know schema 7 — the record schema the 0.5.0 record
model arrives under (ADR-0022) — and SHALL still refuse a schema above it.
A record stamped 7 that carries only fields the earlier schemas admit SHALL
be written and read like any other record; a schema the tool does not know
SHALL be refused at write and at read. A writer SHALL stamp 7 exactly when
its record carries a field a schema-7 family admits: a writer stamps the
least schema the record needs, and a field the session family admits needs
it.

#### Scenario: a record of the newest schema carrying only fields older schemas allow is written and read
- **WHEN** a record stamped 7 carries only fields schemas 1 to 6 admit
- **THEN** it is written and read back unchanged

#### Scenario: the schema above the newest is unknown and refused
- **WHEN** a record is stamped with a schema the tool does not know
- **THEN** it is refused at write and at read

#### Scenario: no writer stamps a schema no field needs
- **WHEN** a `create_*` function or `session_record_schema` builds a record
  carrying no field a schema-7 family admits
- **THEN** the stamped schema stays below 7

#### Scenario: a writer stamps schema 7 when its record needs it
- **WHEN** a `create_*` function builds a record carrying a field a
  schema-7 family admits
- **THEN** the stamped schema is 7
