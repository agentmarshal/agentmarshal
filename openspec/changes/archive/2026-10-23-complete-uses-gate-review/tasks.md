## 1. The gate names the review it passed on

- [x] 1.1 `GateReport` carries `resolved_review` — the id of the
  approving latest review of the resolved commit, or of the
  non-approving one an acceptance covered, none when the gate passed
  on no review — set by the same code that decides the verdict
  check, never recomputed — verify: pytest shows the id on both pass
  paths and none on the no-review path.
- [x] 1.2 `record_commit_completion` takes `resolved_review` and
  reads the advisory ids from the review record carrying that id
  among the records the gate evaluated; without it the review is
  derived as the verdict check does — the latest of the resolved
  commit — so the sidecar call keeps working — verify: pytest.
- [x] 1.3 `complete_task` passes `report.resolved_review` — verify:
  pytest, including a review appended between the gate and the
  disposition check: the passed-on review's advisory findings are
  still owed, an id only the appended review raised is refused, and
  its dispositions land in the record.

## 2. The delta, the transcript and nothing that worked changed

- [x] 2.1 The delta modifies the `finding-lifecycle` requirement
  naming which review's advisory findings need a disposition —
  verify: openspec validate.
- [x] 2.2 Every scenario of the delta is demonstrated by a test
  whose docstring names it — verify: pytest against the delta's
  scenario titles.
- [x] 2.3 The gate's printed transcript is unchanged byte for byte —
  the id rides the report object, not a printed line — and
  `complete --findings` is unchanged — verify: the pinned default
  transcript, the fixtures and the full suite.
- [x] 2.4 The change is archived with the archive command — verify:
  `openspec/changes/archive/` gains the dated directory and
  `openspec/specs/finding-lifecycle/spec.md` gains the modified
  requirement.
- [x] 2.5 The full check sequence passes — `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`,
  `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` —
  and the suite again under CI's conditions, no actor variable and
  no git identity — verify: run them.
