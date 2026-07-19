# CR-007: `agentmarshal status` — task state as a projection

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: done
Completion-Review: CR-007
Reviewed-Commit: 1173631aca483d15dba16490b0b4f3ef87ba35ae
Target-Branch: master
Merged-Commit: a790a0d40ab4ba4f48c1d9469f8d0805fbc66493
Completed-At: 2026-07-19T04:48:01Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-007-completion-1173631aca48.md
Completion-Review-SHA256: sha256:832eeea9f893a29af4ef49761a732897ab851a6b7241ebafb69d1dda31e6c6a5
Scope:
- .agentmarshal/journal/tasks/open/CR-007-status-verb-projections.md
- src/agentmarshal/
- tests/

## Context

ADR-0004 Decision 2: task state is never stored, it is computed
deterministically from the task's records. CR-006 delivered the record
store and the `opened` record; this slice delivers the projection and
the verb that exposes it. With only one lifecycle record type existing
so far the projection is small, but its shape — explicit
record-type-to-state rules, fail-closed on inconsistency — is the
pattern every later verb builds on.

Design constraints (binding):

- Standard library only; `pathlib`; explicit `encoding=` everywhere;
  fail-closed on anything malformed.
- All journal reads go through the existing loaders (`read_records`,
  `parse_contract`) — no direct record/contract parsing anywhere else.
  The loaders' symlink and validation guarantees (CR-006, hardened
  following `project.py`) are inherited, not reimplemented.
- Projection rules are an explicit mapping, not string heuristics.

## Objective

A projection module derives task status from records, and
`agentmarshal status` lists tasks or shows one task's detail.

## Acceptance Criteria

- [ ] A projection function takes a task's validated records (in record
      order) and returns its status: a task with an `opened` record is
      `open`. A task directory whose records lack an `opened` record —
      including an empty records directory — is an error, not a
      default. Unknown record types are already rejected by the loader.
- [ ] `agentmarshal status` inside an initialized project lists every
      task under `journal/tasks/` sorted by id: id, projected status,
      title from the contract header. With no tasks it prints a short
      "no tasks" message and exits 0.
- [ ] `agentmarshal status CR-NNN` prints one task's detail: id,
      status, title, scope paths, and each record's id, type and
      `created_at`. An unknown task id is a clear error, exit non-zero.
- [ ] Fail-closed behavior: outside an initialized project — error,
      non-zero; a malformed record or contract encountered anywhere is
      an error naming the offending file, never silently skipped.
- [ ] Tests cover: listing after `open` (status `open`; a Cyrillic
      title displayed intact); the detail view fields; empty journal;
      unknown task id; a records directory without an `opened` record;
      a malformed record file surfacing as an error with the file path;
      a BOM-prefixed contract.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No new record types, no lifecycle transitions beyond `open`, no
  amendments, no gate integration, no JSON output mode.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
