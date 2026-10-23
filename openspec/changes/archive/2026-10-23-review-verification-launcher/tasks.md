## 1. The sections on the verdict and the launched record

- [x] 1.1 `_VERDICT_OPTIONAL` admits `verification` and `evidence`;
  `_NO_CLASSES` generalizes to `_VERDICT_ABSENT`; `_parse_verdict`
  returns both raw values appended to its tuple — verify: `pytest`.
- [x] 1.2 `_verdict_verification` and `_verdict_evidence` reduce the raw
  values beside `_verdict_classes`, dropping each malformed part with a
  warning naming it — against the record layer's
  `_VERIFICATION_SECTIONS`/`_VERIFICATION_ENTRY_KEYS` and the usable
  string shape the record rules require — verify: `pytest`.
- [x] 1.3 `_verdict_protocol` gains the two keys and the "unconfirmed"
  line; the commit prompt's prose instruction gains the criterion-
  coverage ask; the pinned-prompt tests update — verify: `pytest`.
- [x] 1.4 `_launch_review_tail` runs the reductions after the subject
  check and `_record_launched_review` writes through
  `create_review_record(verification=..., evidence=...)` — verify:
  `pytest`.

## 2. The delta, the docs and nothing that worked changed

- [x] 2.1 The delta adds the launcher requirements to `review-evidence`,
  every scenario demonstrated by a test whose docstring names it —
  verify: `openspec validate`, `pytest`.
- [x] 2.2 `docs/quickstart.md`'s verdict-protocol section states
  `verification` and `evidence` — verify: `pytest` (`test_quickstart`).
- [x] 2.3 A verdict without the sections records exactly as before;
  `submit-review` is untouched; the gate's fixtures are unchanged —
  verify: `pytest`.
- [x] 2.4 `openspec archive` moves the change into place — verify: the
  archive run.
- [x] 2.5 Full check sequence plus the CI-conditions suite — verify:
  green.
