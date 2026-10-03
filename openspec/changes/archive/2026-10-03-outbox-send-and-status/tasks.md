# Tasks

## 1. Escaped printable names

- [x] 1.1 Every name `outbox check` prints or scans goes through the
  escaped printable form — `os.fsencode` then a `backslashreplace`
  decode, the leak scan's header form — so a non-UTF-8 name no longer
  crashes the command and a marker in such a name is still masked —
  verify: the test named after the new check scenario.

## 2. `outbox send`

- [x] 2.1 `send` runs `_run_check` first and refuses on any non-zero
  result — verify: the test named after the scenario commits nothing on a
  non-conforming draft.
- [x] 2.2 `send` refuses when `git diff --cached` names anything outside
  `.agentmarshal/upstream/` — both halves of a staged rename counted,
  paths masked and escaped — verify: the test named after the scenario.
- [x] 2.3 Otherwise `send` stages only `.agentmarshal/upstream` (`git add
  --force`), refuses an empty batch, makes exactly one commit whose
  message names the staged outbox paths, and prints `git rev-parse HEAD`
  — verify: the tests named after the scenarios.
- [x] 2.4 Git runs with `subprocess` and `capture_output` like gate's
  `_run_git_bytes`; failures are masked messages, never tracebacks; in a
  sidecar the commit lands in the journal repository — verify: the
  tests.

## 3. `outbox status`

- [x] 3.1 `status --index <file>` refuses a missing or unreadable index
  and a missing outbox with messages — verify: the tests named after the
  scenarios.
- [x] 3.2 `status` parses every `Source:` line — bare and
  markdown-decorated — into entries identified by line number, hashes
  each regular outbox file with sha256 lowercase hex, prints each file as
  claimed or unclaimed, lists index entries claiming no file, and names
  non-regular or unreadable entries as not hashed with a non-zero exit —
  verify: the tests named after the scenarios.
- [x] 3.3 Every printed name is masked and non-UTF-8 names are escaped —
  verify: the test named after the scenario.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv sync --locked; uv run agentmarshal validate; uv run pytest;
  uv run ruff check; uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` carries each requirement exactly once
  and the change sits under `openspec/changes/archive/`.
