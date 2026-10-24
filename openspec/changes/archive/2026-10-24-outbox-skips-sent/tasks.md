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

## 3. Review-round hardening

- [x] 3.1 The leak scan covers the manifest's next content — the bytes
  `send` stages under `SENT` — so a hit refuses the run like any other
  — verify: `test_the_manifests_next_content_goes_through_the_leak_scan`.
- [x] 3.2 A file name that could add a line to the manifest is refused,
  named escaped, in `check`/`send`; the manifest parses strictly — one
  `<64 hex>  <name>` line each, name without line-forging characters —
  verify: `test_a_file_whose_name_could_add_a_line_to_the_manifest_is_refused`,
  `test_a_manifest_line_in_another_shape_lists_nothing`.
- [x] 3.3 `send` refuses "no drafts to send" before touching the index
  when every entry is already sent — a sent draft renamed leaves the
  operator's staged rename exactly as found — verify:
  `test_send_refuses_a_rename_of_an_already_sent_draft`.
- [x] 3.4 design.md states what the code does on the name/digest
  matching; the delta notes the manifest is bookkeeping, not a finding.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv run agentmarshal validate; uv run pytest -q; uv run ruff check;
  uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` carries each requirement exactly once
  and the change sits under `openspec/changes/archive/`.
