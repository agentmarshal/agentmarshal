# record-schema Specification

## Purpose
How record validation knows which rules a record answers to. A record
written now is checked by every rule the tool knows — at write time, while
the author can still fix the input — and a record read back is checked only
by the rules of the schema it carries, so a rule a later schema introduces
cannot refuse history. One table binds each read-time rule to the schema it
applies from, and writers stamp the least schema their record's fields and
values need, which is how an earlier release's pinned installation keeps
reading a journal a newer one writes to.

## Requirements

### Requirement: A record is checked by the current rules at write time and by the rules of its own schema at read time
At write time the writer SHALL check a record by every rule the tool knows,
whatever schema the record carries: refusal is in place while the author can
still fix the input. At read time a record SHALL be checked only by the rules
of its own schema and below — a rule bound to a later schema does not apply
to it, so a rule a schema introduces cannot refuse history written before
it. The write side (`validate_record_for_write`, and
`validate_record_content` as the gate runs it on the records a candidate
adds and as backfill and migrate run it before writing) applies the first;
the read side (`read_records`, and so validate and status over the journal)
applies the second.

#### Scenario: a record a candidate adds is checked by every current rule
- **WHEN** a candidate adds a record stamped below the schema a rule needs —
  a coordination session stamped 3, or a record bound to a finding stamped 3
- **THEN** the check the gate runs on added records refuses it, while the
  same record already in the journal is read under its own schema's rules

#### Scenario: a record is checked by every current rule at write time
- **WHEN** a rule bound to a schema one above the highest supported is
  registered and a record of the highest schema is presented for write
- **THEN** the record is refused, the later rule applied to it anyway

#### Scenario: a later rule does not reach a record of an earlier schema on read
- **WHEN** a rule bound to a schema one above the highest supported is
  registered and a record of the highest schema is read
- **THEN** the record is accepted, checked by the rules of its own schema
  and below

#### Scenario: a record an earlier release wrote stays valid
- **WHEN** a record written under schema 1 or schema 2 is read back
- **THEN** it validates under the rules of its own schema, the way an
  earlier release's journal must keep reading

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
would apply to old records. A rule SHALL NOT be checked without an
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
  coordination activity (6) and the shared field validators (7)

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
coordination activity stamps 6 — exactly the numbers the writers stamp
today.

#### Scenario: each writer stamps the minimum schema its record needs
- **WHEN** a `create_*` function or `session_record_schema` builds a record
- **THEN** the stamped schema is 3 for the base model and exactly 4, 5 or 6
  where the record's own fields and values require them

### Requirement: Schema 7 is a supported record schema
Record validation SHALL know schema 7 — the record schema the 0.5.0 record
model arrives under (ADR-0022) — and SHALL still refuse a schema above it.
A record stamped 7 that carries only fields the earlier schemas admit SHALL
be written and read like any other record; a schema the tool does not know
SHALL be refused at write and at read. Until a field family of schema 7
registers, no writer SHALL stamp 7: a writer stamps the least schema the
record needs, and no field yet needs it.

#### Scenario: a record of the newest schema carrying only fields older schemas allow is written and read
- **WHEN** a record stamped 7 carries only fields schemas 1 to 6 admit
- **THEN** it is written and read back unchanged

#### Scenario: the schema above the newest is unknown and refused
- **WHEN** a record is stamped with a schema the tool does not know
- **THEN** it is refused at write and at read

#### Scenario: no writer stamps a schema no field needs
- **WHEN** a `create_*` function or `session_record_schema` builds a record
  while no field of schema 7 exists
- **THEN** the stamped schema stays below 7

### Requirement: The record types are declared once
Every record type SHALL be declared once, in one registry that gives, per
type: the predicate type it is projected to, the task state it projects,
the terminal states after which it is admitted, whether a writer may write
it, and whether `recorded_by` with `recorded_by_source` is required of it.
The predicate-type table, the status projection's state table, the set of
types admitted after a terminal record and the writable types SHALL be
derived from the registry — or pinned equal to it by a test — so the
declaration cannot drift into three lists again.

#### Scenario: the three modules read the one registry
- **WHEN** the predicate types, the projected states, the after-terminal
  admissions, the writable types and the recorder requirements are read
- **THEN** each names exactly the types the registry declares, with the
  registry's own values

#### Scenario: a type that requires its recorder refuses a record that names none
- **WHEN** a record of a type the registry marks as requiring its recorder
  carries neither `recorded_by` nor `recorded_by_source`
- **THEN** it is refused

### Requirement: Shared field validators apply from schema 7
The field families of schema 7 SHALL share four validators: a text field
bounded by a number of characters, a text field bounded by a number of
UTF-8-encoded bytes, a JSON field bounded by a number of bytes after
canonical encoding, and the forgeable-text rule over the new displayed
strings. Each validator SHALL read a field registration — which fields it
guards and with what bound — so a field family registers its fields into
the validators it needs and nothing more. A validator SHALL apply only
where a field is registered for it, and only to records whose own schema
reaches the validator's binding.

#### Scenario: a registered text field over its character bound is refused
- **WHEN** a field registered with a character bound carries more
  characters than the bound
- **THEN** the record is refused

#### Scenario: a registered text field over its byte bound is refused
- **WHEN** a field registered with a byte bound encodes to more UTF-8
  bytes than the bound
- **THEN** the record is refused

#### Scenario: a registered JSON field over its canonical byte bound is refused
- **WHEN** a field registered with a byte bound encodes, canonically, to
  more bytes than the bound
- **THEN** the record is refused

#### Scenario: a registered displayed string that could forge a line is refused
- **WHEN** a field registered under the forgeable-text rule carries a
  character that could add a line to rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a registered field within its bounds is admitted
- **WHEN** a field registered with a bound carries a value inside it
- **THEN** the record is admitted

#### Scenario: a schema-7 validator does not reach a record of an earlier schema on read
- **WHEN** a record stamped below 7 carries a field a schema-7 validator
  guards
- **THEN** it is read under its own schema's rules, while the same record
  presented for write is refused
