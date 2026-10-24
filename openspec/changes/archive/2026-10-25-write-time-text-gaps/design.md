## Context

`records.py` validates a record against every rule registered in `_RULES` at
write, and at read applies only the rules bound at or below the record's own
schema through `_RULE_FROM_SCHEMA` (ADR-0015). The forgeable-text rule is one
of those entries, applied by field name; `validate.py` additionally reports an
`artifacts` `ref` carrying a refused character on the read side. `write_record`
serialized the record to text, created the destination exclusively, then wrote
— so a value UTF-8 cannot encode left an empty file. `_utc_timestamp` parsed
with `datetime.fromisoformat`, which accepts any single character as the
date-time separator, so a refused character rode a timestamp past the parse.
`review.py` decoded the reviewer's output with `errors="replace"` and kept the
decoded copy on rejection, losing invalid bytes.

## Decisions

- Timestamps refuse before parsing: `_utc_timestamp` runs the forgeable-text
  check on the raw value, since the parse itself admits refused characters as
  separators. This covers `created_at` and the schema-7 session timestamps in
  one place.
- The artifact-`ref` check is a new write-time rule, not a line inside an
  existing one: it registers as its own entry bound to the first schema after
  today's, so it applies to every record written now — gate candidates
  included — and reaches no record a read can load. `validate`'s read-side
  report stays the reader's only answer for history (ADR-0015 decisions 2
  and 4).
- `write_record` encodes the serialized record to bytes before calling
  `_create_exclusive`, and writes those bytes: an unencodable value fails
  before the file exists rather than inside `TextIOWrapper.write`.
- Rejected output is preserved as received: `_preserve_output`, `_reject` and
  `_parse_verdict` take the reviewer's raw bytes, `_parse_verdict` decoding a
  copy for parsing. `str` remains accepted for text the launcher itself
  builds.

## Alternatives considered

- Checking each timestamp field in `_FORGEABLE_TEXT_FIELDS`: `created_at` is
  checked only inside `_utc_timestamp`, which the read side also runs — the
  same early-refusal semantics apply either way, but the parser-side check
  covers every caller of the one timestamp rule.
- Binding the new rule to schema 7: that would refuse historical records on
  read, exactly what ADR-0015 forbids.

## Risks

- None for valid input: every byte an earlier release wrote still reads, and
  `validate` still reports rather than refuses a historical forged `ref`.
