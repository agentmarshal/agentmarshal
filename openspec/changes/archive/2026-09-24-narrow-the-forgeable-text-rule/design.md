## Context

`_reject_control_characters` in `records.py` refuses a value when any character
has `isprintable() is False` and is not U+0020. It guards review finding ids and
advisory finding ids, acceptance fields and finding ids, a finding record's
summary, and an artifact reference. `reject_control_characters` in
`contracts.py` applies the same test, without the space exception, to `scope`
and `documents` entries (through `validate_scope_entry`) and to the `decisions`
and `extensions` header entries. Both raise
`… must not contain control characters`. A third copy of the test, written
inline, guards a review artifact's `ref` in `validate.py` — on the read side,
where this task's retroactivity applies.

Validation runs on read as well as on write: `validate` loads every task, and
loading validates each record. So a rule tightened in a release reaches records
an earlier release wrote.

## Goals

- Refuse what can add a line to generated text, or hide and reorder it.
- Accept everything else, including space separators.
- Keep one decision point per side (records, contracts).

## Non-Goals

- Rules scoped to the schema that introduced them (its own decision record).
- An allowlist of records accepted as they are.
- Escaping on display instead of refusing.

## Decisions

- **The refused set is named by Unicode category, not by a printability test.**
  `Cc` (C0 and C1 controls) covers `\n`, `\r` and the rest; `Zl` is U+2028 and
  `Zp` is U+2029, the two separators that a renderer may treat as line breaks.
  `unicodedata.category` gives this directly, from the standard library.
- **The bidirectional characters are refused too**, by codepoint: the marks
  U+061C, U+200E and U+200F, the embeddings and overrides U+202A–U+202E, and the
  isolates U+2066–U+2069. All are category `Cf`, so a category rule alone would
  let them through, and each can make displayed text read in an order the bytes
  do not have — the same class of harm as forging a line, and the reason the set
  is not simply "no line breaks". The `Cf` characters left out (U+00AD,
  U+200B–U+200D, U+FEFF) affect neither line breaks nor order; a private-use
  codepoint (category `Co`) renders as one unknown glyph. Both are accepted.
  This is a deliberate boundary, not an oversight.
- **An unpaired surrogate is refused** (category `Cs`). The printability test
  refused it as a side effect and that side effect is worth keeping on purpose:
  such a value cannot be encoded as UTF-8, so a record carrying one could not be
  written back out of the journal it was read from.
- **The third call site joins the other two.** `validate.py` checked an artifact
  `ref` with its own copy of the printability test. Two narrowed copies and one
  left stricter would be exactly the drift this change removes, so it calls the
  same predicate.
- **Space separators are accepted**, U+00A0, U+2007, U+2009 and U+202F
  included. They render as a space; nothing about them can produce a line.
- **The message stays as it is.** `… must not contain control characters` is
  what adopters' tooling and our own tests already read, and it is still true
  of the narrowed set.
- **One function per side.** Records keep `_reject_control_characters`;
  contracts keep `reject_control_characters`; the character predicate itself
  lives once, in `records.py`, and `contracts.py` calls it. The space exception
  disappears: it existed only to undo the printability test, and the new rule
  never refuses a space.

## Risks

- [A future renderer treats some accepted character as a line break] → then the
  set grows by codepoint, and the reason is stated where the set is. The rule is
  now a named set rather than a proxy test, so such a change is visible.
- [Records written between 0.4.0 and this fix were refused, not written] → a
  write refused nothing to the journal; no record needs repair.
