## Context

`forges_rendered_text` in `records.py` names the characters a record's or a
contract header's text may not carry — Unicode categories `Cc`, `Cs`, `Zl`,
`Zp` and the bidirectional marks, embeddings, overrides and isolates — and
writers refuse a value that holds one. Under ADR-0015 a record is checked at
write time by the current rules and at read time by the rules of its own
schema, so a record written before the rule existed — or around the writer,
with a lowered schema — reaches a renderer still carrying them. `status` and
`report` print record and contract values as they stand today: a newline
would print a line the tool never said (including one that reads as an
approval), and an override would reorder what is seen.

## Goals

- One function escapes exactly the refused set, reaching the same predicate
  the writer consults so the write and display sides cannot drift.
- Every record- or contract-derived string `status` and `report` print goes
  through it; the tool's own fixed text is untouched.
- A record carrying no refused character renders byte-identically.

## Non-Goals

- The gate's transcript, the brief and the reviewer prompt — a later task.
- Any change to what is refused at write, or to which rules apply at read.

## Decisions

- **One predicate decides both sides.** `escape_for_display` asks
  `forges_rendered_text` of each character rather than keeping a character
  set of its own; the test derives its cases from the predicate, so the day
  the rule and the escape disagree the test fails — in either direction.
- **Escape where a line is built from a record value.** In the per-task view
  the dispatch escapes the line a renderer returns, so a renderer added
  later cannot forget it; in the task list and in `format_report` each
  interpolated value is escaped, because their tab separators are structure
  and must survive.
- **`\n`, `\r`, `\t` by name, `\uXXXX`/`\UXXXXXXXX` for the rest.** The named
  forms are what a reader expects for the common line-breakers; the generic
  form keeps every other refused character visible and unambiguous — the
  bidirectional controls included, which would otherwise stay invisible.
