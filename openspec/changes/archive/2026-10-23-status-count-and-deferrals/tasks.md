## 1. The count line

- [x] 1.1 `print_task_detail` prints one line `changes_required verdicts
  for <task>: N (threshold T)` when the task has at least one
  `changes_required` review over its candidates — counted over every
  review record of the task with the gate's definition since CR-168
  (a review bound to a research finding is not counted), the threshold
  through `changes_required_threshold` (default 3) — verify: the count
  and finding-bound-review tests (pytest).
- [x] 1.2 When the count reaches the threshold the line is marked
  `(threshold T reached — stop and revisit the contract)`; a malformed
  threshold is named `(threshold unreadable: <error>)`; the line blocks
  nothing — verify: the marked-count and malformed-threshold tests
  (pytest).

## 2. The deferrals section

- [x] 2.1 For a task whose `completed` record carries
  `advisory_dispositions`, `status <task>` prints `Deferrals:` then one
  line per `deferred` finding naming the id, the reason and — when
  present — the `follow_up` task with its state when the journal holds
  it, or `not held by the journal`; `fixed` and `rejected` entries are
  counted on one `fixed=N rejected=M` line, not listed — verify: the
  deferrals test (pytest).

## 3. Nothing else changes

- [x] 3.1 A task with no `changes_required` verdict and no dispositions
  prints today's detail view byte for byte; every new line goes through
  `escape_for_display` — verify: the byte pin and the escaping test in
  `test_status_count_deferrals.py` (pytest); the `status` example in
  `docs/sidecar.md` needs no edit.
- [x] 3.2 The full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`; and the suite passes in
  CI's conditions — `env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1 uv run pytest -q` — verify: run them.
