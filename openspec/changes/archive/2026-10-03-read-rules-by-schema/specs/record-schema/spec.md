## Purpose
How record validation knows which rules a record answers to. A record
written now is checked by every rule the tool knows — at write time, while
the author can still fix the input — and a record read back is checked only
by the rules of the schema it carries, so a rule a later schema introduces
cannot refuse history. One table binds each read-time rule to the schema it
applies from, and writers stamp the least schema their record's fields and
values need, which is how an earlier release's pinned installation keeps
reading a journal a newer one writes to.

## ADDED Requirements

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
the rule applies from. Every rule that exists today applies from schema 1
except the field gates already bound to schemas 2, 4, 5 and 6, which keep
their numbers: provenance from 2, the finding record and finding bindings
from 4, `reviewed_contract` from 5, the coordination activity from 6. A rule
SHALL NOT be checked without an entry in the table, and a read path SHALL
apply no rule whose entry is missing. The schema-version check is a
precondition of the table itself — it is what makes the record's number
known — so it runs ahead of every rule and holds no entry. Some rules
compare a record with where it lies: `task` against the task the record
is written to or read from, `record_type` against the file name that
carries it, a finding binding against the findings the task holds. Such a
rule SHALL be bound in the table like any other and SHALL apply where the
path supplies that placement — the read path supplies the directory and
the file name; the write side supplies the destination and, where the
task's findings are at hand, the finding set. A rule whose placement a
path does not supply SHALL NOT be applied there.

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
  finding record and its bindings (4), `reviewed_contract` (5) and the
  coordination activity (6)

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
