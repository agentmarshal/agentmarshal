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

## 2. `outbox check` — conformance

- [x] 2.1 Every regular file except `README.md` is a draft; a draft missing
  a field or holding only the scaffold's placeholder is named with each
  missing/unfilled field; a fresh scaffold is unfilled in Symptom,
  Measurements and Expected — verify: the tests named after the scenarios.
- [x] 2.2 A non-UTF-8 file is named as such and its bytes are still
  searched — verify: the test named after the scenario.

## 3. `outbox check` — leak scan and exit status

- [x] 3.1 Built-in signatures via `scan_for_leaks` and configured markers
  by position produce per-file `LeakHit`s rendered unbounded by
  `render_leak_hits`; every printed name goes through `safe_path` — verify:
  the tests named after the scenarios, including a marker-named file.
- [x] 3.2 Exit status is 0 only when all drafts conform and the scan finds
  nothing — verify: the tests for each failure alone and for the pass.

## 4. Closeout

- [x] 4.1 Full CI sequence green from the worktree root — verify:
  `uv sync --locked; uv run agentmarshal validate; uv run pytest;
  uv run ruff check; uv run ruff format --check; uv run mypy`.
- [x] 4.2 Archive the change with `openspec archive` — verify:
  `openspec/specs/outbox/spec.md` exists with the Purpose and the three
  requirements, and the change sits under `openspec/changes/archive/`.
