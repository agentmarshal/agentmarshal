## Why

ADR-0022 brings 0.5.0's new fields and record types under one record
schema — 7 — and puts limits on the new fields alone (section 8): an
excerpt of 4 KiB, a payload of 64 KiB, a reason of 1000 characters, and
the forgeable-text rule over the new displayed strings. CR-145 gave
record validation a rule table by schema. Before the field families
arrive, schema 7 must be a number the validator knows, the record types
must be declared in one place — they are listed in three today:
`records.py`'s field sets, `attestation.py`'s predicate types, and
`status.py`'s projection tables — and the limits the new fields share
must exist as rules of schema 7, so each later task only registers its
fields or its record type.

## What Changes

- Schema 7 joins the supported record schemas; schema 8 stays unknown and
  refused. A record stamped 7 that carries only fields the earlier
  schemas admit is written and read; no writer stamps 7, because no field
  requires it yet.
- One registry declares each record type once: its predicate type, the
  state it projects, the terminal states after which it is admitted,
  whether it is writable, and whether `recorded_by` with
  `recorded_by_source` is required of it. The registry lives in
  `attestation.py` — the small module `records.py` and `status.py` both
  import — and `PREDICATE_TYPES`, the state table, the after-terminal set
  and the writable types are derived from it; the writable-type `Literal`
  and the registry's reach into `status.py` are pinned equal by tests.
  `finding`'s recorder requirement moves onto the registry flag with no
  change in behaviour.
- Four shared field validators — text bounded by a number of characters,
  text bounded by a number of UTF-8-encoded bytes, JSON bounded by a
  number of bytes after canonical encoding, and the forgeable-text rule —
  are registered in the rule table as their own entries bound to schema
  7, each reading a field registration. No production field uses them
  yet; tests exercise them through a test-only field.

## Capabilities

- modified: `record-schema`

## Impact

Nothing that schemas 1 to 6 accept or refuse changes: no rule bound to
schema 7 touches an older record on read, no writer's stamped number
moves, and the gate's fixtures stay as they are. The tasks that bring
the new field families and record types each register into the tables
this change lays down — a field into the families and validators, a
record type into the registry — and change nothing else.
