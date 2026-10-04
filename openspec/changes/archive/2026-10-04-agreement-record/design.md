## Context

ADR-0018 decision 2 decided that agreement with the contract can be
recorded: a declared actor states agreement with the contract at a stated
hash, any declared actor may record it, and there are no roles. ADR-0022
section 3 gave `agreement` schema 7, one field — `contract`, the hash
agreed with — and the `recorded_by`/`recorded_by_source` pair required,
as on `check`, `acknowledgement` and `finding`. CR-154 laid down how a
record type is declared once — `RECORD_TYPES` in `attestation.py`,
everything else derived or pinned — and how a field family registers;
CR-170 registered the closest precedent, `acknowledgement`. CR-163's
`contract` field on `opened` and `amendment` is the same field this type
carries, so it reuses that family's shape rule rather than writing a
second one.

## Goals

- An `agreement` record type exists from schema 7: a claim admitted
  after no terminal record, writable, `recorded_by` with
  `recorded_by_source` required.
- Its one own field: `contract` — required — exactly 64 lowercase hex
  characters, the form `contract_sha256` produces and `opened`/
  `amendment` carry.
- An `agreement` record on a schema below 7 is refused at write and on
  read; writing one stamps 7.
- `validate` and `status` handle a task carrying one without failing,
  and the gate admits a candidate adding one exactly as it admits the
  other schema-7 types the projection admits before a terminal record.

## Non-Goals

- The `agree` command, comparing the agreed hash with the contract's
  current or pinned hash, the gate's `require_agreement` check, and how
  `status` shows agreement or its absence — all later tasks.
- Roles or any restriction on who may agree (ADR-0018 decision 2).
- Protection beyond what the published decisions promise — see
  docs/threat-model.md — including against processes of the same OS
  user.

## Decisions

- **The type declares once in `RECORD_TYPES`.** Predicate
  `https://agentmarshal.dev/attestations/agreement/v1`,
  `projects_to=None` — an agreement changes no task state —
  `admitted_after_terminal` empty, `writable`,
  `requires_recorded_by=True`: an agreement names who agreed, and any
  declared actor may write it, so admission is the pair the registry
  already expresses. A recorder that is not a declared actor is still
  accepted, as on the other schema-7 types that require `recorded_by`
  (ADR-0022 section 3). Everything else derives: `PREDICATE_TYPES`, the
  projection's state, terminal and after-terminal tables, the writable
  set the guard and the write path consult. The two hand-written places
  a new type still touches get theirs: `_RECORD_FIELDS` gains
  `"agreement"`, `WritableRecordType` gains `"agreement"`, and the
  pinning tests gain the literals.
- **`contract` registers through the contract family's own frozenset** —
  `(7, "agreement", _SCHEMA_7_CONTRACT_FIELDS)` beside the `opened` and
  `amendment` entries: it is the same field, so the same set and the
  same shape rule. `_RECORD_FIELDS["agreement"]` holds the envelope
  alone; below 7 the family's field is not admitted, so a record
  carrying it is refused at write and, on read, by the field-admission
  rule of the record's own schema.
- **No second shape rule.** `contract-hash-7` already refuses a
  `contract` that is not exactly 64 lowercase hex wherever the field is
  carried — registered ahead of the family's rule, it fires first. The
  family's own rule, `agreement-fields-7`, bound to 7 like
  `check-fields-7` and `acknowledgement-fields-7`, adds only what is
  different here: `contract` is required — an agreement states agreement
  with a contract *at a hash*, so a record carrying none states nothing.
- **The record-type gate is its own rule bound to 1**, like `check` and
  `acknowledgement`: `agreement` refuses `record_type: agreement` below
  schema 7 whatever the record carries — it guards admission, not
  history, and no legitimate history can carry the type.
- **`("agreement", "contract")` registers into `_FORGEABLE_TEXT_FIELDS`**
  the same way the contract family registers on `opened` and
  `amendment`: the entry never fires, the 64-hex shape rule standing
  first, but the family registers its displayed string. No length table
  gains an entry — ADR-0022 section 8 bounds `excerpt`, `payload` and the
  new record types' `reason` alone, and `agreement` carries no `reason`.
- **`_minimum_schema` raises to 7 on the type** — `record_type ==
  "agreement"`, the `check` and `acknowledgement` precedent — and
  `create_agreement_record` builds the record through the same one
  derivation, stamping 7.

## Published requirements checked and left alone

- contract-governance's "An opened or amendment record may carry the
  contract's hash" and "The contract field is refused below schema 7"
  speak of the types that pin the hash; `MAY` admits without reserving
  the field to them, so both stay literally true with `agreement`
  carrying it too. "A contract hashes one way however it is read" is
  about `contract_sha256`, unchanged. The `status` drift requirement
  compares against `opened`/`amendment` pins alone — an agreement is not
  a pin, and nothing in it changes.
- record-schema's registry requirement is about the mechanism — every
  record type declared once, the derived surfaces pinned — which the
  registration satisfies; its rule-table requirement already covers "the
  schema-7 field families' own shape rules" bound to 7, which
  `agreement-fields-7` is. Its "a writer stamps 7 exactly when its
  record carries a field a schema-7 family admits" stands as it did for
  `check` and `acknowledgement`: a writer-built agreement always carries
  `contract`.
- record-lifecycle admits "a measurement in any terminal state, and a
  reopening after completion": `agreement` is admitted after no terminal
  record, so the sentence stays true of it.
- docs/threat-model.md's forgeable-text enumeration lists `opened` and
  `amendment`'s `contract` but not `agreement`'s — docs/ is outside this
  change's scope; the omission is named in the report.

## Risks

- [A hand-made `agreement` record stamped below 7 with no `contract`
  reads] → the `agreement` rule bound to 1 refuses the type below its
  schema, and one carrying `contract` is refused by `fields` anyway.
- [An `agreement` record a candidate adds names no recorder] →
  `requires_recorded_by` makes the recorded-by rule refuse it; the write
  path stamps the pair from the environment before writing.
- [A second 64-hex rule could drift from `contract-hash-7`] → the type
  reuses the contract family's rule and frozenset; `agreement-fields-7`
  checks presence only.
- [The registry pinning tests enumerate the types literally] → they are
  updated with the new literals in the same change, so the drift the
  pins exist to catch cannot pass silently.
