## Why

ADR-0018 decision 1: the `opened` record and every `amendment` carry the
sha256 of the contract text they establish, in the lowercase hex
`reviewed_contract` already uses; ADR-0022 section 2 puts the field in
schema 7. Today the review launcher hashes text read with newline
translation, while the gate reads raw `git show` output — the same
contract could hash two ways on a checkout with CRLF line endings. One
function must serve every place that hashes a contract, and the records
that establish a contract must be able to carry its hash before the
transition task writes it.

## What Changes

- `contract_sha256` in `contracts.py` is the one way a contract is
  hashed: the contract's bytes as stored or read decode as UTF-8 — a
  byte-order mark kept the way text reading keeps it — CRLF and lone CR
  translate to LF the way Python's text reading translates them, and the
  lowercase hex sha256 of the result encoded as UTF-8 is returned. Bytes
  that do not decode as UTF-8 are refused with a message naming the
  source.
- The review launcher computes `reviewed_contract` with it; for every
  contract the launcher reads today the value is unchanged, so
  review-evidence's requirement stays true.
- From schema 7, an `opened` record and an `amendment` record may carry
  `contract` — the hash as exactly 64 lowercase hex characters —
  registered through the record-type registry's field families as the
  session fields of CR-160 were: the field is optional, passes the
  forgeable-text rule registered for the record type and field, carries
  no length bound, and below 7 is refused at write and on read by the
  field-admission rule. A record carrying it stamps 7; one without it
  stamps what it stamps today.
- `create_opened_record` and `create_amendment_record` accept the hash as
  an optional argument; no caller passes it yet.

## Capabilities

- modified: `contract-governance`

## Impact

No writer sets the field yet — `open`, `amend` and `migrate` are the
transition task — and no reader of it exists, so the gate's fixtures are
unchanged. The launcher's `reviewed_contract` is byte-identical to
today's, which the both-ways test pins over LF, CRLF and BOM-bearing
inputs.
