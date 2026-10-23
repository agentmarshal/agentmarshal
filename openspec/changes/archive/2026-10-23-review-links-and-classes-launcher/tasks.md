## 1. The link and the classes on the launched record

- [x] 1.1 `_VERDICT_OPTIONAL` admits `classes`; `_parse_verdict` returns
  the raw value unvalidated — verify: `pytest`.
- [x] 1.2 `_verdict_protocol` lists the vocabulary and asks for one class
  per finding id; `_review_prompt`, `_finding_review_prompt` and
  `_dry_run_prompt` take `vocabulary`; the pinned-prompt tests update —
  verify: `pytest`.
- [x] 1.3 `launch_review` and `_launch_finding_review` read
  `review.finding_classes` from the journal repository — the default when
  unset — and capture the task's latest review id before the reviewer
  runs — verify: `pytest`.
- [x] 1.4 `_launch_review_tail` normalizes `classes` — a vocabulary hit
  recorded, an unknown class `other` with a warning naming the id and the
  class, an id the verdict does not carry dropped with a warning, a
  malformed `classes` dropped whole with a warning — and the launched
  record is written through `create_review_record` with
  `previous_review`/`classes`, the prose pin before the write as before —
  verify: `pytest`.

## 2. The delta, the docs and nothing that worked changed

- [x] 2.1 The delta adds the launcher requirements to `review-evidence`,
  every scenario demonstrated by a test whose docstring names it —
  verify: `openspec validate`, `pytest`.
- [x] 2.2 `docs/quickstart.md`'s verdict protocol states `classes`, the
  `other` mapping and the previous-review link — verify: `pytest`
  (`test_quickstart`).
- [x] 2.3 A verdict without `classes` records exactly as before; a first
  review carries no `previous_review`; `submit-review` writes no link;
  the gate's fixtures are unchanged — verify: `pytest`.
- [x] 2.4 `openspec archive` moves the change into place — verify: the
  archive run.
- [x] 2.5 Full check sequence plus the CI-conditions suite — verify:
  green.
