## 1. The flags

- [x] 1.1 `record_session` accepts `commit`, `model`, `trace`,
  `cli_session`, `report_ready` and `fallback_reason` as optional
  keyword arguments and passes them to `create_session_record` —
  verify: pytest.
- [x] 1.2 `record-session` accepts `--commit`, `--model`, `--trace`,
  `--cli-session`, `--report-ready` and `--fallback-reason`, each
  optional; `--commit` resolves through the gate's `_resolve_commit`
  against `placement.host_root` — the host in a sidecar — and a
  revision git cannot resolve is refused naming it — verify: pytest.
- [x] 1.3 Every delta scenario has a test whose docstring names it —
  verify: pytest -q.

## 2. Nothing that worked changed

- [x] 2.1 `--outcome` stays free text; a session recorded without the
  flags stamps the schema it had (3, or 6 for coordination); every
  existing record-session test is unchanged — verify:
  `uv run pytest -q`.
- [x] 2.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`,
  `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` —
  verify: run them.
- [x] 2.3 Archive with
  `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2 archive
  record-session-schema-7-flags --yes` — verify: the delta lands in
  `openspec/specs/session-activity/spec.md` and the change moves under
  `openspec/changes/archive/`.
