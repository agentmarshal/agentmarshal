## 1. The projection

- [x] 1.1 `report.py` derives each task's lead-time boundaries —
  `opened`, the first implementer session's `started_at`, the first
  review, the first approving review and the last completion — marking
  `unknown` where a record exists but lacks the time and `not yet`
  where the event has no record, never substituting a session's
  `created_at`; the durations between consecutive boundaries; the
  review rounds in order with verdicts and elapsed times; and the
  lead-time aggregate over `done` tasks — verify: pytest.
- [x] 1.2 `report --task` prints the task line it prints today, then a
  `Phases` line, a `Durations` line and one `Round` line per review;
  `report` appends a `Lead` line after the summary — today's lines
  byte for byte first, record values escaped on display — verify:
  pytest.

## 2. Scenarios and documentation

- [x] 2.1 Every delta scenario has a test whose docstring names it —
  verify: `uv run pytest -q`.
- [x] 2.2 The existing tests pinning today's output are updated to the
  new appended lines — verify: `uv run pytest -q`.
- [x] 2.3 `docs/sidecar.md`'s `report --task` example shows exactly
  what the command prints for that example — the record times
  included — and nothing else in the document changes.

## 3. Checks and archive

- [x] 3.1 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`; the suite also passes in
  CI's conditions — no actor variable and no git identity: `env -u
  AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  uv run pytest -q` — verify: run them.
- [x] 3.2 Archive with `OPENSPEC_TELEMETRY=0 npx -y
  @fission-ai/openspec@1.13.2 archive report-lead-time --yes` —
  verify: the delta lands in `openspec/specs/session-activity/spec.md`
  and the change moves under `openspec/changes/archive/`.
