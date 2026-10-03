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
  --force` — a file an ignore rule names is checked and sent like every
  file), refuses an empty batch, makes exactly one commit whose message
  names the staged outbox paths, and prints `git rev-parse HEAD` —
  verify: the tests named after the scenarios.
- [x] 2.4 Git runs with `subprocess` and `capture_output` like gate's
  `_run_git_bytes`; failures name only the subcommand — never the
  arguments, one of which is the commit message — masked, never
  tracebacks; in a sidecar the commit lands in the journal repository —
  verify: the tests.
- [x] 2.5 `send` refuses "no drafts to send" when the outbox holds only
  the README — verify: the test named after the scenario.
- [x] 2.6 Before the add, `send` pins every regular outbox file's blob
  id (`git hash-object`); after the add, `ls-files --stage` must show
  exactly those paths at stage 0 with those ids — a changed, removed or
  newly arrived file refuses and the index goes back — verify: the test
  named after the scenario.
- [x] 2.7 A failed `git commit` unstages exactly what `send` staged —
  the pre-add `ls-files --stage -z` records replayed through
  `update-index --index-info` plus `update-index --force-remove` for the
  additions, so no object id is written and the repository's object
  format cannot break the restore — and the restore runs only on a
  refusal, never after a made commit — verify: the tests named after
  the scenarios, in sha1 and in sha256 repositories.

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
- [x] 3.4 An index entry is identified by its digest, its line kept for
  the report: two digests on one line are two entries, and an unmatched
  digest is listed once however many lines carry it — verify: the tests
  named after the scenarios.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv sync --locked; uv run agentmarshal validate; uv run pytest;
  uv run ruff check; uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` carries each requirement exactly once
  and the change sits under `openspec/changes/archive/`.
