## 1. The read

- [x] 1.1 `report.py` defines the unmeasured predicate once — a session
  record whose every token count is zero and which carries no `usage`
  key — verify: pytest.
- [x] 1.2 `report.py` leaves unmeasured sessions out of the per-task
  and aggregate token sums and of `_cost_sums`' sums and counts, and
  carries their count on `TaskReport` and `JournalReport` — verify:
  pytest.

## 2. The views

- [x] 2.1 `format_report` appends `unmeasured=<n>` as the last field of
  the task line, the summary line and every `Cost` line whenever the
  scope left sessions out as unmeasured — byte-for-byte today when it
  left none — verify: pytest.
- [x] 2.2 `status_view.py` renders a session record through
  `_RECORD_RENDERERS`, appending ` tokens=unmeasured` under the shared
  predicate and printing the generic line unchanged for every other
  session — verify: pytest.

## 3. Scenarios and pins

- [x] 3.1 Every delta scenario has a test whose docstring names it —
  verify: `uv run pytest -q`.
- [x] 3.2 The existing status and report tests pass unchanged — a
  journal with no unmeasured session prints byte-for-byte today —
  verify: `uv run pytest -q`.

## 4. Checks and archive

- [x] 4.1 Full check sequence passes: `uv run agentmarshal validate`,
  `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`,
  `uv run mypy` — verify: run them.
- [x] 4.2 Archive with `OPENSPEC_TELEMETRY=0 npx -y
  @fission-ai/openspec@1.13.2 archive unmeasured-session-usage --yes`
  — verify: the delta lands in `openspec/specs/session-activity/spec.md`
  and the change moves under `openspec/changes/archive/`.
