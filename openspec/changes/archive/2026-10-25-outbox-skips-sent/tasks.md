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
  and a line that does not parse refuses the check, the manifest and
  the line's number named — verify:
  `test_a_file_whose_name_could_add_a_line_to_the_manifest_is_refused`,
  `test_a_manifest_line_in_the_wrong_form_refuses_the_check`,
  `test_a_manifest_line_whose_name_is_refused_refuses_the_check`,
  `test_a_manifest_line_ending_in_a_carriage_return_refuses_the_check`,
  `test_send_refuses_a_manifest_line_that_does_not_parse`.
- [x] 3.3 With no new draft `send` still commits a change the outbox
  holds to a file already sent — a rename, a move inside the outbox —
  the message naming both paths of a rename and the manifest following
  the new name; with no draft and no such change it refuses "no drafts
  to send" — verify:
  `test_a_draft_renamed_since_the_last_batch_is_sent_as_a_rename`,
  `test_send_commits_a_rename_of_a_file_already_sent`,
  `test_send_refuses_when_every_file_is_already_sent`.
- [x] 3.4 design.md states what the code does on the name/digest
  matching; the delta notes the manifest is bookkeeping, not a finding.
- [x] 3.5 Masking runs on the raw shown name before display escaping —
  a signature beside a control character still masks — verify:
  `test_a_secret_beside_a_control_character_in_a_name_is_masked`.
- [x] 3.6 The manifest is pinned once, on the content `send` writes —
  verify: `test_the_sent_manifest_is_pinned_once_with_the_content_send_writes`.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv run agentmarshal validate; uv run pytest -q; uv run ruff check;
  uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` carries each requirement exactly once
  and the change sits under `openspec/changes/archive/`.
