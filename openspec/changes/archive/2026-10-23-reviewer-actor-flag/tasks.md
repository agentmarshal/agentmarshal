## 1. The flag on both commands

- [x] 1.1 The `submit-review` and `review` parsers take an optional
  `--actor <id>` — verify: `--help` lists it on both (pytest).
- [x] 1.2 `submit_review` takes `reviewer_actor`, refuses a value the
  record rule refuses before `load_task_for_record` naming `--actor`,
  passes it to `create_review_record`, and `SubmittedReview` gains
  `actor_note` — the "not a declared actor" note, computed against the
  journal project's `actors` keys through `_project_root_for` — verify:
  pytest.
- [x] 1.3 `launch_review`, `_launch_finding_review` and
  `_launch_review_tail` take and thread `reviewer_actor` to the same
  `submit_review` call — the refusal runs before the reviewer command —
  and `LaunchedReview` gains `actor_note` — verify: pytest asserts the
  reviewer stub was never invoked (pytest).
- [x] 1.4 `dry_run_review` takes `reviewer_actor` and refuses an invalid
  one before the reviewer command runs; the CLI admits `--actor` beside
  `--dry-run`, shows the actor a recorded review would carry and prints
  the same undeclared note — verify: pytest.

## 2. The delta and nothing that worked changed

- [x] 2.1 The delta adds the requirements to `review-evidence`, every
  scenario demonstrated by a test whose docstring names it — verify:
  openspec validate, pytest.
- [x] 2.2 A review written without `--actor` is byte-for-byte the record
  the previous release wrote, apart from its id and times, and every
  printed line is unchanged — verify: the pinning test (pytest).
- [x] 2.3 `recorded_by` and `reviewer.actor` stay independent; no other
  command changes and the gate's fixtures are untouched — verify: the
  independence test, the full suite green, `tests/fixtures/` untouched
  (pytest).
- [x] 2.4 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/review-evidence/spec.md` gains the requirements.
- [x] 2.5 Full check sequence passes — `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — and the suite again
  under CI's conditions, no actor variable and no git identity —
  verify: run them.
