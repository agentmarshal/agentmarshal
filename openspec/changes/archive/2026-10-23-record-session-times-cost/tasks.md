## 1. The flags

- [x] 1.1 `record_session` accepts `started_at`, `ended_at`,
  `resets_at`, `cost_amount`, `cost_currency`, `cost_source` and
  `if_missing` as optional keyword arguments, turns the record rules'
  refusals into flag-named refusals before anything is written, passes
  the fields to `create_session_record` (the cost assembled as its
  `{"amount", "currency", "source"}` object) and returns the written
  path or the existing record's id — verify: pytest.
- [x] 1.2 `record-session` accepts `--started-at`, `--ended-at`,
  `--resets-at`, `--cost-amount`, `--cost-currency`, `--cost-source`
  and `--if-missing`, each optional; a refused value is refused naming
  the flag and writes nothing; `--if-missing` prints one line naming
  the existing record on a match — verify: pytest.
- [x] 1.3 Every delta scenario has a test whose docstring names it —
  verify: pytest -q.

## 2. Nothing that worked changed

- [x] 2.1 A session written with today's flags is the record the
  previous release wrote, apart from id and times — a test pins it;
  every existing record-session test is unchanged — verify:
  `uv run pytest -q`.
- [x] 2.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`,
  `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` —
  verify: run them.
- [x] 2.3 Archive with
  `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2 archive
  record-session-times-cost --yes` — verify: the delta lands in
  `openspec/specs/session-activity/spec.md` and the change moves under
  `openspec/changes/archive/`.
