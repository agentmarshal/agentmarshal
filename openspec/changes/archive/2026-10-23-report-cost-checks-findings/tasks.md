## 1. The projections

- [x] 1.1 `report.py` sums each task's session `cost` per currency —
  `reported` and `estimated` apart, `decimal.Decimal` sums printed in
  plain decimal notation, nothing converted — counts the sessions
  carrying no cost, and counts the distinct commits a `check` record
  marked `failed` or `error`, per task and in aggregate — verify:
  pytest.
- [x] 1.2 `report.py` projects the findings view — the classes recorded
  on reviews with counts and up to three example ids each, and the
  `deferred` advisory dispositions still open (no `follow_up`, or a
  follow-up the journal does not hold as completed) with task, finding
  id, reason and follow-up — verify: pytest.

## 2. The views

- [x] 2.1 `report --task` prints the task's `Cost` lines after the
  round lines, then `Checks	rejected_commits=N` and the
  observer-declaration note; `report` appends the `Cost` lines, the
  `Checks` line and the note after `Lead` — today's lines byte for byte
  first, record values escaped — verify: pytest.
- [x] 2.2 `cli.py` adds `--findings` to the `report` parser;
  `report --findings` prints the findings view — `Classes` lines then
  `Deferrals` lines, `(none)` markers for empty sections — and `--task`
  scopes it — verify: pytest.

## 3. Scenarios and pins

- [x] 3.1 Every delta scenario has a test whose docstring names it —
  verify: `uv run pytest -q`.
- [x] 3.2 The existing tests pinning today's output are updated to the
  new appended lines — verify: `uv run pytest -q`.

## 4. Checks and archive

- [x] 4.1 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`; the suite also passes in
  CI's conditions — no actor variable and no git identity: `env -u
  AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  uv run pytest -q` — verify: run them.
- [x] 4.2 Archive with `OPENSPEC_TELEMETRY=0 npx -y
  @fission-ai/openspec@1.13.2 archive report-cost-checks-findings
  --yes` — verify: the deltas land in `openspec/specs/session-activity/spec.md`
  and `openspec/specs/finding-lifecycle/spec.md`, and the change moves
  under `openspec/changes/archive/`.
