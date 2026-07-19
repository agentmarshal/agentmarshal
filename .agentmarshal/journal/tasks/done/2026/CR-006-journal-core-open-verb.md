# CR-006: journal core and the `agentmarshal open` verb

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: done
Completion-Review: CR-006
Reviewed-Commit: 0fc2497d12c991cd8328e284723cc442896ea513
Target-Branch: master
Merged-Commit: 9d86870ac35830d6e0e20359aeb96d5b3d8586fb
Completed-At: 2026-07-19T03:59:17Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-006-completion-0fc2497d12c9.md
Completion-Review-SHA256: sha256:34ba5eb581bbe8dbd8bfa988797fbf2efb908789c430a7cc7040ed944f37a943
Scope:
- .agentmarshal/journal/tasks/open/CR-006-journal-core-open-verb.md
- src/agentmarshal/
- tests/

## Context

ADR-0004 fixed the journal data model: human-authored contracts with a
machine-readable TOML header, append-only JSON evidence records written
by trusted recorders with collision-resistant identifiers, state as a
projection. This task cuts the first vertical slice of that model: the
journal core package and the first protocol verb, `agentmarshal open`.

Design constraints (ADR-0004, binding):

- Standard library only. TOML is read with `tomllib`; no YAML anywhere.
- Records are JSON, one file per record, created with exclusive-create
  semantics (an existing path is an error, never an overwrite).
- Record identifiers are ULID-class: 48-bit millisecond timestamp plus
  80 random bits, Crockford base32, lexicographically sortable —
  implemented in the standard library (`time`, `secrets`), no
  dependency.
- Validation is fail-closed: unknown schema version, missing required
  field or malformed content is an error. Every record and contract
  header carries `schema = 1`.
- `pathlib` everywhere; every `open()` passes `encoding=`; files are
  written UTF-8 without BOM with LF endings; reads tolerate a BOM.
- The journal root is `<project-root>/.agentmarshal/journal` (constant
  for now); a v2 task lives under `journal/tasks/<TASK-ID>/`.

## Objective

A `journal` package provides contract-header parsing, an append-only
record store and the opened event; `agentmarshal open` allocates the
next task id and creates the task's contract skeleton plus its opened
record.

## Acceptance Criteria

- [ ] `src/agentmarshal/journal/` provides: parsing of a contract
      markdown file whose TOML header sits between `+++` delimiter
      lines (fields: `schema = 1`, `id`, `title`, `scope` array,
      `acceptance` array of strings); a ULID generator as specified
      above; `write_record`/`read_records` over
      `journal/tasks/<id>/records/<ulid>-<type>.json` with
      exclusive-create; an `opened` record type carrying `schema`,
      `record_type`, `task`, `created_at` (UTC ISO-8601) and the
      recording tool's version.
- [ ] `agentmarshal open --title <text> [--scope <path> ...]` run
      inside an initialized project: allocates the next id `CR-NNN` by
      scanning existing `journal/tasks/` entries (serialized task
      creation per ADR-0002 makes locking unnecessary), writes
      `journal/tasks/CR-NNN/contract.md` (TOML header filled; body
      sections Context / Objective / Acceptance Criteria / Non-Goals as
      placeholders) and the `opened` record, prints the created paths,
      exits 0.
- [ ] Fail-closed behavior: outside an initialized project — clear
      error, exit non-zero, nothing created; target task directory
      already existing — error, nothing modified.
- [ ] Tests cover: ULID uniqueness and lexicographic ordering across
      calls; header parsing (valid, missing required field, unknown
      schema version, BOM-prefixed file); exclusive record creation
      (second write of the same path fails, content preserved);
      `open` in a fresh initialized repo (files exist, header and
      record parse back cleanly); `open` outside a project fails
      closed; id allocation increments past existing tasks; a title
      containing Cyrillic text round-trips correctly.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No `status`/projections beyond writing the opened record (next
  slice), no `abandon`, no contract amendments, no gate integration,
  no migration of the v1-format journal, no new dependencies.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
