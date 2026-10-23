## 1. The flags and the write

- [x] 1.1 The `complete` parser takes repeatable `--disposition
  <id>=<disposition>[:<reason>]` and `--follow-up <id>=<task>` —
  verify: pytest exercises both flags.
- [x] 1.2 `record_commit_completion` reads the advisory ids of the
  review the gate passed on — `reviews[-1]` of the resolved commit, as
  the gate's verdict check reads it — requires a `--disposition` per
  advisory finding, folds `--follow-up` into its entry, and writes them
  through `create_completed_record`'s `advisory_dispositions`;
  `complete_task` and the sidecar's commit lane both go through it —
  verify: pytest, including the acceptance-covered and sidecar cases.
- [x] 1.3 Every refusal precedes the write and writes nothing: each
  unanswered advisory finding named, each unknown id named,
  `deferred`/`rejected` without a reason, `follow_up` on a
  non-`deferred`, a record-rule refusal repeated naming the flag, and
  a malformed or repeated flag — verify: pytest asserts the refusal and
  that no `completed` record exists.
- [x] 1.4 `complete --findings` refuses the flags and gains no refusal
  for want of a disposition — verify: pytest.

## 2. The delta, the doc and nothing that worked changed

- [x] 2.1 The delta adds the requirements to `finding-lifecycle` and
  modifies the requirement whose "Nothing reads the field yet" is now
  false — verify: openspec validate.
- [x] 2.2 Every scenario is demonstrated by a test whose docstring
  names it — verify: pytest against the delta's scenario titles.
- [x] 2.3 `docs/quickstart.md` says `complete` asks for a disposition
  per advisory finding, with the flag syntax — verify: the quickstart
  test still passes.
- [x] 2.4 A review with no advisory findings completes exactly as
  before — no flag, no field, same record; no other command changes;
  the gate's fixtures and every pinned transcript are untouched —
  verify: the no-advisory test, the full suite, `tests/fixtures/`
  untouched.
- [x] 2.5 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/finding-lifecycle/spec.md` gains the requirements.
- [x] 2.6 The full check sequence passes — `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — and the suite again
  under CI's conditions, no actor variable and no git identity —
  verify: run them.
