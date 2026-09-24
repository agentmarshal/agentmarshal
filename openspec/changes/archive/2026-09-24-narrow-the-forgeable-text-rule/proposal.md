## Why

A record's string fields are refused when they contain a character for which
`str.isprintable()` is false. That test is false for all sixteen `Zs` space separators
except U+0020 — among them U+00A0, U+2007, U+2009, U+202F and U+3000 — and none
of those can end a line, which is the only thing the rule exists to prevent: a value must not be
able to add a line to generated text, including one that reads as an approval.

An adopter hit this on the published 0.4.0. Eleven occurrences of U+202F, used
as a thousands separator inside finding-id text, in three review records written
by 0.1.0, make whole-journal `validate` exit 1. Their journal passes under
0.3.0: the check is older, but 0.4.0 extended it from acceptance finding ids to
review `findings` and `advisory_findings`, and record validation runs on read.
The records cannot be repaired — both tasks are closed and the journal is
append-only — so the upgrade is blocked.

## What Changes

The rule refuses the characters that can add a line, reorder text, or fail to
encode: categories `Cc`, `Zl`, `Zp` and `Cs`, and the bidirectional marks,
embeddings, overrides and isolates (U+061C, U+200E, U+200F, U+202A–U+202E,
U+2066–U+2069). Everything else is accepted, space separators included. One
predicate decides it for all three places that ask — records, contract headers,
and the artifact reference `validate` reports — and none of them consults
`str.isprintable()`.

## Capabilities

- new: `record-text-safety`

## Impact

A journal refused by 0.4.0 over a space separator validates again. Values that
could forge a line are refused exactly as before. No record changes, and no
allowlist is introduced.
