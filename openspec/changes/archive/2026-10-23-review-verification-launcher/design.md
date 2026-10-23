## Context

`src/agentmarshal/journal/review.py` builds the reviewer prompt, runs the
reviewer command in a metadata-free snapshot, parses the verdict block it
prints and writes the record itself — CR-185's tail, which already reduces
a verdict's `classes` the same way this change reduces `verification` and
`evidence`: the verdict is a paid run's output, so markup the record
cannot hold is dropped with a warning, never refused. The record rules
the launcher must preempt live in `records.py`'s `review-fields-7` rule:
`verification` is a non-empty object of only `executed`, `read` and
`not_run`, each a non-empty array, `read` of strings and the other two of
exact-key objects, every string non-empty and forgeable-free; `evidence`
is a non-empty object keyed by the record's own finding ids with
non-empty forgeable-free values.

## Goals

- The verdict protocol admits optional `verification` and `evidence`;
  the prompt asks for them, for evidence per finding id, and — on the
  commit binding — for each criterion's place in the diff and its
  demonstrating test, and states the "unconfirmed" advisory rule of
  ADR-0017 decision 5.
- The launcher records the sections and entries the record rules admit
  and drops each malformed part with a warning naming it; an `evidence`
  entry for an id the verdict does not carry is dropped with a warning.
- A verdict without the sections records exactly as before — no fields,
  no schema rise from them; `submit-review`, the gate's fixtures and
  every other command stay as they are.

## Non-Goals

- `submit-review` flags for these fields; `status` and `report` surfacing.
- Verifying what the reviewer says it ran — the sections are a
  declaration, as ADR-0017 decision 2 frames `check` records.
- Requiring the sections: they stay optional forever.

## Decisions

- **One sentinel for every absent optional key.** `_NO_CLASSES`
  generalizes to `_VERDICT_ABSENT`: a key whose value is `null` is a
  malformed value the launcher drops with a warning, while an absent key
  records nothing — the distinction `classes` already needed.
- **Parse raw; normalize after the subject check.** `_VERDICT_OPTIONAL`
  admits `verification` and `evidence`; `_parse_verdict` returns their
  values unvalidated, appended to its result tuple so the `classes`
  position is unmoved. After the reviewed-subject check, beside
  `_verdict_classes`, `_verdict_verification` and `_verdict_evidence`
  reduce each to what the record rules admit, landing warnings on the
  diagnostics channel.
- **Drop the malformed part, record the rest.** For `verification` the
  parts are keys and entries: a key outside the three sections drops
  with a warning naming it; a section that is not a non-empty array
  drops with a warning; inside a section, each malformed entry — a
  `read` item that is no usable string, an `executed`/`not_run` entry
  that is not an object carrying exactly its keys with usable string
  values — drops with a warning naming the section and the position,
  the section's surviving entries are recorded, and a section left with
  none lands nothing. For `evidence` the parts are entries: an id the
  verdict does not carry drops with a warning naming it, and a value
  the record could not hold drops with a warning naming the id. A
  `verification` or `evidence` that is not an object, or is empty, drops
  as a whole with a warning — the same whole-drop `classes` applies,
  while the per-part drop preserves what `classes`' coverage rule did
  not need: the good half of a mixed object.
- **The section vocabulary is the record layer's.** The launcher imports
  `records.py`'s `_VERIFICATION_SECTIONS` and `_VERIFICATION_ENTRY_KEYS`
  — the same sharing precedent as `_REVIEW_VERDICTS` — so what the
  launcher calls a section can never drift from what the record admits.
- **The asks split by binding.** `verification`, `evidence` and the
  "unconfirmed" line join `_verdict_protocol`, which both bindings
  share. The criterion-coverage ask is commit-only — a finding review
  has no diff — so it lands in the commit prompt's prose instruction,
  not the shared one. The mark "unconfirmed" lives on the finding's
  prose line, the only channel a finding id has for a qualifier.
- **The tail writes the two fields.** `_record_launched_review` gains
  `verification=`/`evidence=` and hands them to
  `create_review_record`, the way `previous_review`/`classes` already
  pass — the record layer's own validation stays the last word.

## Risks

- [A forgeable string inside a section would reach the record and refuse
  the paid verdict] → the per-entry drop checks
  `forges_rendered_text` before writing, exactly what the record rule
  would refuse — the verdict stands and the warning names the part.
- [Half-dropped sections confuse a reader] → each drop warns, so a
  record's silence about a section is never silent: stderr names every
  part that did not land.
- [A prompt that asks for nothing it can parse] → the protocol text
  names the exact shapes the record rules admit, and the pinned-prompt
  tests hold it.
