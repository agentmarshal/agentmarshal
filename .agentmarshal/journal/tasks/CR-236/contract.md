+++
schema = 2
id = "CR-236"
title = "Write-time text safety covers schema-7 timestamps and review artifact references, a write never leaves an empty record file, and refused reviewer output is kept byte for byte"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/review.py",
  "tests/",
  "openspec/changes/write-time-text-gaps/",
  "openspec/changes/archive/",
  "openspec/specs/record-text-safety/",
]
acceptance = [
  "a timestamp field (`created_at` and the schema-7 `started_at`, `ended_at`, `resets_at`) that contains a character the forgeable-text rule refuses (a Cc or Cf character, a lone surrogate, a line or paragraph separator) is refused at write time with a message naming the field, before any file is created (release-audit finding AUD-gate-journal-2); the comment in records.py claiming each timestamp shape admits no such character is made true",
  "`write_record` encodes the record to bytes before creating the file, so no failure while encoding leaves an empty or partial record file in the journal; a test forces an encoding failure and shows no file remains",
  "a review record's artifact reference containing a character the forgeable-text rule refuses is refused by the same write-time validation the gate uses for added records (`validate_record_content`), as record-text-safety requires (AUD-gate-journal-3); reading follows ADR-0015 — a record an earlier release wrote is still reported by `validate` as today, not newly refused on read",
  "refused reviewer output is preserved byte for byte: the bytes the reviewer printed are what the preserved file holds, including bytes that are not valid UTF-8, while parsing still uses the decoded text (AUD-gate-journal-6; docs/quickstart.md says the raw output is kept); a test with invalid UTF-8 shows identical bytes",
  "the change write-time-text-gaps carries a delta on record-text-safety that names the timestamp fields among the values the write-time rule covers (ADDED, or MODIFIED with the full current text, heading byte for byte and every scenario); each scenario is demonstrated by a test whose docstring names it; archived with the archive command (OpenSpec 1.15.0)",
  "valid records are written byte for byte as today; existing tests and transcripts are unchanged; the suite and the full CI sequence pass",
]
documents = ["openspec/specs/record-text-safety/"]
decisions = ["ADR-0015", "ADR-0022"]
+++

# Write-time text gaps

## Context

Release audit 0.6.0, area gate-journal, findings AUD-gate-journal-2, -3
and -6 (confirmed by reproduction): Python's `fromisoformat` accepts any
character as the date-time separator, so a timestamp can carry a newline,
a bidirectional control or a lone surrogate — the last reaches exclusive
file creation and leaves a zero-byte record that makes `validate` and
`report` fail. ADR-0022 decision 8: every displayed string the new fields
introduce follows the forgeable-text rule at write time. A review
artifact reference is checked only by `validate`, not at write time,
although record-text-safety requires the refusal at write time. Refused
reviewer output is decoded with replacement before it is preserved.

## Objective

Nothing the forgeable-text rule refuses reaches the journal through a
timestamp or an artifact reference, no write leaves a broken file, and
the evidence of a refused review is the reviewer's bytes.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any other field or record rule.
- Rewriting records already in a journal.
