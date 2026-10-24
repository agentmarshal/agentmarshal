## ADDED Requirements

### Requirement: The write path refuses what could still slip the text boundary
A record's `created_at` and a session's `started_at`, `ended_at` and
`resets_at` SHALL refuse a character the forgeable-text rule refuses ahead
of the parse, which accepts any single character as the separator; an
`artifacts` `ref` SHALL refuse the same through the shared write path.
Record bytes SHALL encode fully before exclusive creation, so a failure
leaves nothing behind, and a refused reviewer's output SHALL be kept raw.
Timestamp and `ref` refusals SHALL reach no record a read can load.

#### Scenario: a timestamp carrying a refused character is refused
- **WHEN** `created_at` or a session's `started_at`, `ended_at` or
  `resets_at` contains a character the forgeable-text rule refuses — a
  newline, a bidirectional mark standing in for the separator, or a lone
  surrogate
- **THEN** the write is refused before any file is created, and the message
  names the field, while a record an earlier release wrote still reads and
  validates, never refused on read

#### Scenario: an artifact ref carrying a refused character is refused at write
- **WHEN** a record's `artifacts` `ref` contains a character the
  forgeable-text rule refuses — on a record written or on a candidate
  `validate_record_content` checks for the gate
- **THEN** it is refused and the message names the field, while a record an
  earlier release wrote still reads and is reported by `validate`, never
  refused on read

#### Scenario: a failure while encoding leaves no file
- **WHEN** record bytes fail to encode — a value carrying an unpaired
  surrogate no record rule reached
- **THEN** no file is created: the record serializes and encodes before its
  destination is exclusively created

#### Scenario: rejected output is kept as the bytes the reviewer wrote
- **WHEN** a reviewer's output is refused — by verdict parsing or by record
  validation — and carries bytes that are not valid UTF-8
- **THEN** the kept file holds the reviewer's bytes unchanged, the verdict
  having parsed from a decoded copy
