## Context

CR-193 moved the mark-building into `capture.py` so the gate could
share it, and left `cli.py` its private copies as a deferred one-line
switch — the review correctly found the design's "cannot drift" claim
false while the copies remained. CR-190's review found the mark masked
in code but promised only as escaped in the specification, and the
archived design claiming the matched text could not reach it;
`acknowledge.py`'s docstring still denying any honouring; and two test
gaps — the sidecar read path the requirement names and the `--help`
verification a task claimed.

## Goals

- One function builds the mark: `_acknowledgement_mark` in
  `capture.py`, called by `leak-scan` and by the gate, its helper
  `_acknowledgement_identification` beside it.
- The specification states the mark as it is: who acknowledged and the
  reason masked by the scan and escaped on display, and the one
  mark-builder the two surfaces share.
- The untrue document claims carry dated corrections; `acknowledge.py`'s
  docstring describes the record as honoured.
- The sidecar read path and `leak-scan --help`'s `--task` are pinned
  by tests.

## Non-Goals

- Any change to what the scan matches, to the mark's content or to
  exit statuses — the refactor is a text move, not a behaviour change.
- Rewriting the archived design documents beyond a dated correction.
- Moving the record-reading — `_leak_scan_acknowledgements` is the
  command's own lookup, not the mark.
- Protection beyond the published threat model.

## Decisions

- **The switch is a deletion plus an import.** `cli.py` loses
  `_acknowledgement_identification` and `_acknowledgement_mark`
  verbatim — the texts were already identical — and imports
  `_acknowledgement_mark` from `capture.py`, the same underscore-name
  sharing `_resolve_commit` and `_SESSION_ACTIVITIES` already use.
  `gate.py` needs nothing: it already calls the shared function, so
  the two callers now sit on one implementation and cannot drift.
- **The specification says masked, not only escaped.** The mark's
  `recorded_by` and `reason` are record values the write rules never
  constrained — an operator's name can be the very string the scan
  matches — so the requirement states the mark is masked by the scan
  and escaped on display, and gains the scenario the existing
  masked-recorder test demonstrates. The gate's requirement states the
  mark is the one mark-builder both surfaces share, and the reads
  requirement gains the sidecar scenario the requirement's own
  ADR-0014 sentence describes.
- **The corrections are dated lines, not edits.** Each archived design
  gains one `Correction 2026-10-23 (CR-195)` line saying what was
  untrue — the matched text can reach the mark and the mark was not
  shared — and the rest stands as written: the journal keeps the
  record of what was believed, and the correction keeps the reader
  from taking it as true.
- **The two gaps close where the scenario lives.** The sidecar read —
  records in the journal repository's working tree, the candidate
  resolved and scanned in the host — is exercised in the
  acknowledgement suite beside the reads it names, and `leak-scan
  --help` is pinned listing `--task` the way `acknowledge --help`'s
  flags already are.

## Risks

- [An import cycle from the switch] → none: `cli.py` already imports
  from `capture.py`, and `escape_for_display` stays imported where
  `_acknowledgement_mark` runs, as CR-193's move established.
- [A behavioural drift hiding in the move] → the two texts were
  identical and the whole acknowledgement suite, the gate transcript
  fixtures and the pinned outputs pin both callers byte for byte.
- [A MODIFIED requirement silently dropping a scenario] → the delta
  restates every scenario of the requirements it touches, so the
  archive merge carries each one forward and every scenario keeps the
  test whose docstring names it.

## Open Questions

- None.
