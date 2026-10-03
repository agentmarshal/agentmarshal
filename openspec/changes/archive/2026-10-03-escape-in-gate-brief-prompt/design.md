## Context

`escape_for_display` in `journal/display.py` already renders every
character `forges_rendered_text` refuses as a visible escape — `\n`, `\r`
and `\t` by name, `\uXXXX` (`\UXXXXXXXX` past the Basic Multilingual Plane)
for the rest. CR-155 routed `status` and `report` through it; the gate's
transcript (`gate.py`), the implementer brief (`brief.py`) and the reviewer
prompt (`review.py`, including the amendment history `brief.py` renders for
both) still interpolate record and contract values as they stand. Under
ADR-0015 a record is checked at read time by the rules of its own schema,
so a value a later rule would refuse can still reach these renderers.

## Goals

- Every string the gate, the brief or the reviewer prompt prints that comes
  from a record or a contract goes through `escape_for_display`.
- A record or contract carrying no refused character renders
  byte-identically — the pinned gate fixtures, the pinned prompts and the
  contract-history "no amendments" scenario stay green unchanged.
- Nothing about what is refused at write changes.

## Non-Goals

- The contract document itself, the diff and embedded artifact content.
  Those are blocks the tool presents, not values placed into a line — a
  contract body is multi-line by definition, and escaping it would destroy
  the thing the reviewer is asked to judge.
- Text the tool itself fixedly says, and values that are already
  structurally confined (the `> `-quoted amendment reason keeps its line
  structure; see Decisions).
- Any change to what is refused at write, or to which rules apply at read.

## Decisions

- **One escape point per transcript line in the gate.** Both gate
  evaluations route every line through `escape_for_display` at the point it
  joins the transcript — the finished line, not each interpolation — so a
  check or notice added later cannot forget to escape. The per-task status
  view made the same choice for the same reason (CR-155). The tool's own
  fixed text contains no refused character, so escaping the finished line
  changes nothing but what a record or contract put there; the finding ids,
  acceptance fields, reviewer names, scope entries, artifact references and
  error details the lines interpolate are all record or contract text.
- **The brief escapes at the point a value joins a line.** The briefing is
  a document, not a list of lines, so each interpolated value is escaped:
  scope and acceptance entries, the task id, the names of decisions,
  documents and extensions, the lexical paths the document walk lists, and
  the amendment history's fields. The contract body appended verbatim is a
  block, not a line value.
- **The amendment reason keeps its line quoting.** A reason is prose the
  writer may legitimately give more than one line, and the `> ` quoting is
  what stops a recorded line reading as a heading the history never wrote.
  The renderer splits on `\n` alone — not `splitlines()`, which would also
  break on refused separators like U+2028 and hide them as structure — and
  escapes each rendered line, so every refused character except the real
  newline the quoting is built around prints as its escape. Trailing real
  newlines are stripped before quoting, so a reason that ends in one does
  not close with an empty quoted line. The recorder keeps its whitespace
  fold (a name renders on one line), applied to the escaped name so a
  refused character in it — a newline included — prints as its escape
  rather than folding to a space.
- **The prompt escapes each field it places into a line.** The named
  contract material (decisions, documents, absent extensions), the finding
  id, the claim summary, artifact references and the undecodable-file names
  are each escaped; the contract text, the diff and the prefixed artifact
  content stay verbatim blocks. The amendment history comes from the shared
  renderer, already escaped.
- **Refusals name values escaped too.** Where a refusal or a warning quotes
  a record or contract value — a finding id that is not the task's, an
  artifact reference that drifted, a verdict's echoed subject — the value
  is escaped before it joins the message, so an error line cannot be forged
  either.
