## 1. The none lines

- [x] 1.1 `_assignment_lines` appends `- implementer sessions: (none)`
  when `implementers` is declared and no implementer session is
  recorded, and `- reviews: (none)` when `reviewers` is declared and no
  review is recorded — each where its group's lines would stand, and no
  `(none)` line for a side whose list is not declared — verify: the
  three new tests in `test_status_assignment.py` (pytest).

## 2. Nothing else changes

- [x] 2.1 The tests that pinned the silent ran side now pin the `(none)`
  lines; the byte-for-byte pins and every other test pass unchanged —
  verify: `test_status_assignment.py` and `test_status_view.py`
  (pytest).
- [x] 2.2 The full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`; and the suite passes in
  CI's conditions — `env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1 uv run pytest -q` — verify: run them.
