## 1. The gate

- [x] 1.1 `run_gate` projects every affected task's merged records with
  `project_status` over the union of the target's and the candidate's
  record paths, refuses with one FAIL line naming the task and the
  projection's reason, and applies the same closed-at-base admission to
  every affected task other than the judged one — verify: the tests
  whose docstrings name each scenario (pytest).
- [x] 1.2 A candidate adding records its affected tasks' projections
  admit, or none, produces today's transcript byte for byte — verify:
  the scenario tests and the pinned fixtures (pytest).

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the record-lifecycle
  delta are written — verify: openspec validate.
- [x] 2.2 Every scenario in the delta is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the
  scenario headings.
- [x] 2.3 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv run
  ruff format --check`, `uv run mypy`.
- [x] 2.4 The change is archived with the archive command — verify:
  `openspec/specs/record-lifecycle/spec.md` gains the new requirement
  once and the change lives under `openspec/changes/archive/`.
