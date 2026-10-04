## Why

ADR-0018 decision 2: a record exists for agreement with the contract — a
declared actor states agreement with the contract at a stated hash, and
any declared actor may record it; there are no roles. ADR-0022 section 3
gave the record schema 7 with one field, `contract`, and required
`recorded_by` with `recorded_by_source`. CR-163 gave the one shape the
field takes and pinned the contract's hash on `opened` and `amendment`;
this record states agreement with one such hash. The journal cannot yet
carry an agreement at all.

## What Changes

- An `agreement` record type joins the record-type registry, declared
  once: its predicate type, no projected state, admission after no
  terminal record, writable, `recorded_by` with `recorded_by_source`
  required.
- Its one own field registers through the contract field's schema-7
  family: `contract` — required here — the sha256 of the contract text
  agreed with, exactly 64 lowercase hex characters, the form
  `contract_sha256` produces and `opened`/`amendment` carry; it registers
  under the forgeable-text rule for this record type and field, with no
  length bound.
- An `agreement` record stamped below 7 is refused at write and on read;
  a writer stamps 7 through the minimum-schema derivation, and
  `create_agreement_record` builds the record.

## Capabilities

- modified: `contract-governance`

## Impact

No other record type changes, and the gate's fixtures are unchanged.
`contract` shares the shape rule the contract family already owns — no
second 64-hex rule is written. Nothing reads agreements yet: the `agree`
command, the gate's `require_agreement` check and `status` showing who
agreed are later tasks.
