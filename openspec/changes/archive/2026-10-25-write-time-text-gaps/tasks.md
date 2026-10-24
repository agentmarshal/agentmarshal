## 1. Timestamp safety

- [x] 1.1 `_utc_timestamp` refuses a value carrying a character the forgeable-text rule refuses before `fromisoformat` parses it, naming the field — covers `created_at` and the session's `started_at`, `ended_at` and `resets_at`; the comment claiming the timestamp shape could not carry one is corrected — verify: test per field.
- [x] 1.2 A refusal happens before any file is created — verify: test asserts the journal root never appears.

## 2. Atomic record write

- [x] 2.1 `write_record` serializes with `ensure_ascii=False`, appends the newline and encodes before `_create_exclusive`; the encoded bytes are what the file receives — verify: test forces an encoding failure and asserts no file exists.

## 3. Artifact reference at write

- [x] 3.1 A new write-time rule bound past today's schemas refuses an `artifacts` `ref` carrying a refused character, for `write_record` and `validate_record_content` alike — verify: test through the gate's path.
- [x] 3.2 A record an earlier release wrote still reads and is reported by `validate`, never refused on read — verify: test hand-writes such a record.

## 4. Rejected reviewer output

- [x] 4.1 `_preserve_output`, `_reject` and `_parse_verdict` carry the reviewer's raw bytes; parsing decodes a copy — verify: test keeps invalid UTF-8 byte-for-byte.
