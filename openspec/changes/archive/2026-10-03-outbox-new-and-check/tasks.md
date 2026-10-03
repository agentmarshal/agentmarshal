# Tasks

## 1. The command group and `outbox new`

- [x] 1.1 `src/agentmarshal/outbox.py` registers the `outbox` group and its
  `new`/`check` subcommands from its own module (`register`/`run`); `cli.py`
  gains only the import, the registration line and the dispatch line —
  verify: `agentmarshal outbox --help` lists both subcommands and the
  cli.py diff shows only the hook.
- [x] 1.2 `outbox new "<gist>"` writes `NNNN-<slug>.md` (next free number,
  slug of the gist — the scheme of design.md) with the five `## ` headings,
  Version and Environment filled, prints the path, never overwrites, and
  refuses with a message when the outbox is absent — verify: the tests
  named after the spec scenarios pass.
- [x] 1.3 The outbox is found under the project root in both placements —
  verify: a sidecar test lands the draft in the journal repository's
  `.agentmarshal/upstream/` and not in the host.
- [x] 1.4 Only a name in the exact scheme `new` writes counts toward the
  next number — a hand-written date-prefixed name (`2026-10-03-note.md`)
  is not number 2026 — verify: the test places such a file and the next
  draft is `0001-*`.

## 2. `outbox check` — conformance

- [x] 2.1 Every regular file except `README.md` is a draft; a draft missing
  a field or holding only the scaffold's placeholder is named with each
  missing/unfilled field; a fresh scaffold is unfilled in Symptom,
  Measurements and Expected — verify: the tests named after the scenarios.
- [x] 2.2 A non-UTF-8 file is named as such and its bytes are still
  searched — verify: the test named after the scenario.
- [x] 2.3 An entry that is not a regular file — a directory, a symlink, a
  FIFO — is named as not a draft and not checked and fails the run —
  verify: the test named after the scenario.

## 3. `outbox check` — leak scan and exit status

- [x] 3.1 Built-in signatures via `scan_for_leaks` and configured markers
  by position produce per-file `LeakHit`s rendered unbounded by
  `render_leak_hits`; every printed name goes through `safe_path` — verify:
  the tests named after the scenarios, including a marker-named file.
- [x] 3.2 Exit status is 0 only when all drafts conform and the scan finds
  nothing — verify: the tests for each failure alone and for the pass.
- [x] 3.3 Every entry's file name is scanned like the content — the name
  leaves with the batch — so a marker- or signature-carrying name is a hit
  by itself and fails the check even with clean content — verify: the
  test named after the scenario.
- [x] 3.4 No exception's text reaches the output: an OS error is described
  by `strerror`/errno name only and every printed path goes through
  `safe_path`; markers come from `markers_from_config`, the helper the
  `leak-scan` command uses — verify: the test named after the unreadable
  draft's scenario.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv sync --locked; uv run agentmarshal validate; uv run pytest;
  uv run ruff check; uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` exists with the Purpose and the three
  requirements, and the change sits under `openspec/changes/archive/`.
