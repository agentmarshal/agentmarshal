## 1. The gate's line

- [x] 1.1 `gate.py` computes the candidate's writer-emails set once,
  ahead of the verdict block, shared with the reviewer-independence
  check — verify: pytest.
- [x] 1.2 The acceptance PASS line appends ` (self-accepted: accepting
  party is a declared writer of the candidate)` after the party when
  `accepted_by` case-folded matches the set — byte-for-byte today for
  any other party — verify: pytest.

## 2. The report's line

- [x] 2.1 `report.py` derives a completed task's `decision` from the
  latest review and the latest findings-carrying acceptance bound to
  the `completed` record's own `completed_commit`/`completed_finding` —
  `approved` on an approving latest review, else
  `accepted-over-findings` — and keeps today's rule for a task with no
  `completed` record — verify: pytest.
- [x] 2.2 `report.py` derives `self_accepted` from the decisive
  acceptance's `accepted_by` against the accepted commit's declared
  writers in the placement's host repository, and `format_report`
  appends ` self-accepted` after the decision field — verify: pytest.
- [x] 2.3 `report.py` reuses `status`'s writer lookup and comparison —
  `status_view._is_self_accepted`, imported where it runs since that
  module imports `report` — so the mark is one derivation, carries the
  tri-state through `TaskReport.self_accepted`, and prints
  ` self-acceptance-unchecked` where git cannot answer — verify:
  pytest.

## 3. Scenarios and pins

- [x] 3.1 Every delta scenario has a test whose docstring names it —
  verify: `uv run pytest -q`.
- [x] 3.2 The existing gate, report and status tests and the transcript
  fixtures pass unchanged — a journal with no self-acceptance and no
  earlier-commit acceptance prints byte-for-byte today — verify:
  `uv run pytest -q`.

## 4. Checks and archive

- [x] 4.1 Full check sequence passes: `uv run agentmarshal validate`,
  `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`,
  `uv run mypy` — verify: run them.
- [x] 4.2 Archive with `OPENSPEC_TELEMETRY=0 npx -y
  @fission-ai/openspec@1.15.0 archive self-acceptance-on-every-surface
  --yes` — verify: the delta lands in
  `openspec/specs/operator-acceptance/spec.md` and the change moves
  under `openspec/changes/archive/`.
