## Why

The forgeable-text rule guards the fields it names, but three gaps let a value
reach the journal or the operator around it:

- `datetime.fromisoformat` accepts any single character as the date-time
  separator, so `created_at` and a session's `started_at`, `ended_at` and
  `resets_at` parse a timestamp whose separator is a newline or a bidirectional
  mark — and a lone surrogate parses too, then fails only when the record
  encodes, after its file is already created empty.
- A record's `artifacts` `ref` is checked for a refused character only on read
  by `validate`; nothing refuses it at write or for a gate candidate.
- A refused reviewer's output is kept from a decoded copy, so bytes that are
  not valid UTF-8 are silently replaced — the evidence is not what the
  reviewer wrote.

## What Changes

- `_utc_timestamp` refuses a value carrying a character the forgeable-text
  rule refuses before it parses, naming the field; the comment that claimed
  the timestamp shape could not carry one is corrected.
- `write_record` serializes and encodes the complete record before the
  destination is exclusively created, so an encoding failure leaves no file.
- A new write-time rule bound past today's schemas refuses an `artifacts`
  `ref` carrying a refused character — for `write_record` and the gate's
  `validate_record_content` alike — while no record a read can load is newly
  refused (ADR-0015).
- `_preserve_output`, `_reject` and `_parse_verdict` keep the reviewer's raw
  bytes; parsing decodes a copy with replacements.

## Capabilities

- modified: `record-text-safety`

## Impact

A forged timestamp or artifact reference can no longer be written or added.
An encoding failure leaves no empty record behind. Rejected reviewer output
is preserved byte-for-byte. Existing records read and validate exactly as
before; no record changes.
