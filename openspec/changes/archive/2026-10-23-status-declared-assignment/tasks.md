## 1. The section

- [x] 1.1 `print_task_detail` prints the assignment section between the
  scope block and the record lines when the contract header declares any
  of `implementers`, `reviewers` and `independence`: `Assignment:`, then
  the three declaration lines — the declared lists in their order,
  `(not declared)` for an undeclared field — verify: the declared and
  undeclared-field tests (pytest).
- [x] 1.2 One line per implementer session — a session record whose
  `role` is `implementer` — naming the record id and showing `actor`,
  the vendor from `usage.provider`, `model`, and `fallback_reason` when
  the record carries it; `(absent)` for a value that is not there, the
  vendor never derived from the actor; ` (not declared for the role)`
  when `implementers` is declared and the actor is outside it — verify:
  the implementer-session tests (pytest).
- [x] 1.3 One line per review record naming the record id and showing
  the reviewer's `actor`, `vendor` and `model`, `(absent)` for a value
  that is not there; the same mark when `reviewers` is declared and the
  actor is outside it — verify: the review-line tests (pytest).

## 2. Nothing else changes

- [x] 2.1 Every section line goes through `escape_for_display`; a
  contract declaring none of the three fields prints today's detail view
  byte for byte — verify: the escaping pin and the byte-for-byte test in
  `test_status_assignment.py` (pytest).
- [x] 2.2 The full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`; and the suite passes in
  CI's conditions — `env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1 uv run pytest -q` — verify: run them.
