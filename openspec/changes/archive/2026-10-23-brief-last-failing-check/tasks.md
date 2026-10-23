## 1. The renderer

- [x] 1.1 `brief.py` gains `render_last_failing_check(records)`: the last
  `check` record in record order whose `result` is `failed` or `error`
  yields the `## Last failing check` section — the one-sentence
  observer's-declaration caveat, then `name`, `result`, short `commit`,
  `failed_step`, `run_url` and `excerpt` when carried, each escaped —
  or `""` when the task carries no failing check — verify: the tests
  whose docstrings name the section's scenarios (pytest).
- [x] 1.2 A later `check` record of the same `name` carrying
  `result: passed` and a different `commit` adds the fix line naming
  that commit in short form — same-commit and other-name passes are not
  named — verify: the tests whose docstrings name the three fix
  scenarios (pytest).
- [x] 1.3 `build_brief` attaches the rendered section after the
  amendment history and before the named material — verify: the section
  order and the byte-for-byte pins (pytest).

## 2. Nothing that worked changed

- [x] 2.1 A task with no `check` records yields the brief it yielded
  before, byte for byte; a task whose checks are all `passed` or
  `skipped` the same — verify: the tests whose docstrings name the two
  scenarios (pytest).
- [x] 2.2 Every field value the section prints is escaped — verify:
  the renderer-level escaping test whose docstring names the scenario
  (pytest).
- [x] 2.3 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv run
  ruff format --check`, `uv run mypy`, and the suite again under CI
  conditions — no actor override, no git identity — verify: run them.
