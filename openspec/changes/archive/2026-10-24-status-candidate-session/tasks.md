## 1. The line

- [x] 1.1 `_producing_session_line` returns the line for the commit the
  task's latest review judged: the latest implementer session whose
  `commit` equals the `reviewed_commit`, showing id, actor, outcome and
  `report_ready` when carried, saying the run did not end `implemented`
  when it did not, and counting the earlier naming sessions — `None`
  when there is no review, when the latest review binds a finding, or
  when no implementer session names the commit — verify: the tests
  whose docstrings name each scenario (pytest).
- [x] 1.2 `print_task_detail` prints the line last of the derived
  lines, escaped through `escape_for_display` like every added line —
  verify: the byte-for-byte pin of a task whose candidate no
  implementer session names, plus the existing pins (pytest).

## 2. Checks

- [x] 2.1 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv run
  ruff format --check`, `uv run mypy` — verify: run them; and the CI
  conditions run `env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1 uv run pytest -q`.
