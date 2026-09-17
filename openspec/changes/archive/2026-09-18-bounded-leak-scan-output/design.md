## Context

`render_leak_hits` in `capture.py` caps every rendering at twenty records and
appends "and N more not shown". The gate's transcript line and the standalone
command's stdout both call it, so both are capped. The cap was argued from the
transcript's readability; the command's purpose is the opposite.

## Goals

- Every hit visible where the output is the answer.
- A bounded line where the output is one line of a document.
- One renderer, so a hit's shape cannot differ between the two.

## Non-Goals

- A retention or cleanup policy for what the tool leaves in the system's
  temporary directory. Rejected verdicts, reviewer diagnostics and dry-run
  output all land there and none of them is ever removed; a rule for one of
  them would be a rule for the wrong scope. It is deferred, and this document
  does not point the reader at a record of that deferral, because the register
  it lives in is not published.
- A flag to raise or lower the gate's bound. Nobody has asked for one, and a
  knob would need a home in the project file and a story about the transcript's
  stability.
- Any change to what the gate refuses: the added-content scan stays advisory.

## Decisions

- **The bound is the caller's, the rendering is shared.** `render_leak_hits`
  takes the limit as a parameter: the gate passes its bound, the standalone
  command passes none. The two callers still cannot drift on what a hit looks
  like, which is what CR-100's acceptance criterion bought, and they no longer
  share a bound neither of them declared.
- **The count is part of the bounded rendering, not a second line.** A reader of
  the transcript sees "and N more not shown" in the same line as the hits, so
  the line stays one line and cannot be quoted without its own caveat.
- **Twenty stays the gate's number.** It was chosen in CR-100 and nothing has
  argued against it for the transcript; changing it here would be a second
  decision in a task that exists to remove one.

## Risks

- [The byte-for-byte transcript tests pin the old wording] → they exercise a
  clean candidate with no warning line at all; a candidate with hits is pinned
  by the gate's own leak-scan tests, which state the expected line.
- [An unbounded standalone output floods a terminal] → it is the output the
  operator asked for, and the bounded alternative is what this change removes.
