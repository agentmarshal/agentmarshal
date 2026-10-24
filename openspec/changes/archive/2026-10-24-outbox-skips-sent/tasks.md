# Tasks

## 1. The sent manifest and the skip

- [x] 1.1 `check` reads the outbox's `SENT` when it is a regular file —
  one `<sha256>  <name>` line each — and refuses with a message when it
  cannot be read; `check` and `send` take `--index <file>` and reuse the
  `Source:` parse `status` runs, factored into one helper — verify: the
  tests named after the scenarios.
- [x] 1.2 A regular file whose sha256 a manifest line or an index
  `Source:` line claims is not a draft: still read, pinned and scanned,
  but never field-checked; the command prints `skipped as sent: <n>`
  when it skipped any — verify: the tests named after the scenarios.
- [x] 1.3 A file whose name the manifest carries beside a different
  sha256 is checked like a draft and the check names it as changed
  after sending — an annotation, not a refusal — verify: the test
  named after the scenario.

## 2. `send` records the batch in the manifest

- [x] 2.1 The check computes the manifest's next content — current
  bytes plus one line per draft — and pins `SENT` to that blob id;
  `send` writes exactly those bytes before the add so the batch commit
  carries drafts and manifest together — verify: the test named after
  the scenario.
- [x] 2.2 A batch staging only `SENT` is nothing to send and refuses;
  "no drafts to send" counts drafts under the new rule — verify: the
  tests named after the scenarios.
- [x] 2.3 A refused send puts the manifest's bytes back — or removes it
  — alongside the index restore, so a failed commit never leaves a
  manifest claiming unsent files — verify: the test named after the
  scenario.

## 3. Closeout

- [x] 3.1 Full CI sequence green from the worktree root — verify:
  `uv run agentmarshal validate; uv run pytest -q; uv run ruff check;
  uv run ruff format --check; uv run mypy`.
- [x] 3.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` carries each requirement exactly once
  and the change sits under `openspec/changes/archive/`.
