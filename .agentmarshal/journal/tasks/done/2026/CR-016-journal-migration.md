# CR-016: journal migration tooling (v1 format -> v2 format)

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-26
Status: done
Completion-Review: CR-016
Reviewed-Commit: c866fce6e8efc9686cd7492c9bda0702e0a48599
Target-Branch: master
Merged-Commit: d9aa80b143fb1682b69050491d3aad7a8250d8f5
Completed-At: 2026-07-25T14:52:24Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-016-completion-c866fce6e8ef.md
Completion-Review-SHA256: sha256:6ded0868c9cf460a2184b37a4ae670e0560030a4f90c260809447b8e987ede68
Scope:
- .agentmarshal/journal/tasks/open/CR-016-journal-migration.md
- src/agentmarshal/
- tests/

## Context

Self-hosting requires this repository's own journal — written in the v1
bash format — to be read by the v2 tools (`status`, `gate`, `report`).
This slice delivers the migration tool that converts a v1-format journal
into the v2 data model (ADR-0004). It is also the first exercise of the
migration tooling host-projects will need for their own transition.

The v1 format (source):
- Task files: markdown with `Key: Value` header lines (`Owner`, `Type`,
  `Created`, `Status` one of open/in_review/done/abandoned,
  `Reviewed-Commit`, `Merged-Commit`, `Completed-At`, a `Scope:` list),
  then a markdown body; the title is the first `# CR-NNN: ...` line.
  Files live under `tasks/open/`, `tasks/done/<year>/`,
  `tasks/abandoned/`, `tasks/backlog/`.
- Review files: markdown under `reviews/<year>/` with a machine header
  (`Task`, `Reviewer-Role`, `Reviewer-Vendor`, `Reviewer-Model`,
  `Reviewer-Email`, `Reviewed-Commit`, `Verdict`, `Finding-IDs`).

The v2 format (target, ADR-0004): `tasks/<TASK-ID>/contract.md` (TOML
header + body) and append-only JSON records under
`tasks/<TASK-ID>/records/`.

Design constraints (binding):

- Standard library only; `pathlib`; explicit `encoding=`; fail-closed on
  any unparseable/inconsistent input (never silently drop a task or
  review).
- Reuse the v2 record factories and validators (`create_opened_record`,
  `create_review_record`, `create_completed_record`,
  `create_abandoned_record`, `write_record`) and the contract writer /
  parser — the migrated output must pass the same validation as native
  v2 records, and re-project to the same lifecycle state.
- **Non-destructive:** read the v1 journal, write a fresh v2 journal to a
  separate output directory; never mutate the source. The operator
  verifies, then swaps during cutover.
- Deterministic ordering of emitted records per task (opened first, then
  reviews in reviewed-time/file order, then the terminal record) so the
  projection is stable.

## Objective

`agentmarshal migrate-journal --source <v1-journal> --target <v2-journal>`
converts a v1-format journal to the v2 data model, fail-closed, and
verifies the result re-projects each task's terminal state.

## Acceptance Criteria

- [ ] `agentmarshal migrate-journal --source <dir> --target <dir>` reads
      every v1 task file (open/done/abandoned/backlog) and emits, per
      task, a v2 `tasks/<id>/contract.md` (TOML header: schema=1, id,
      title from the `# CR-NNN:` line, scope from the `Scope:` list,
      acceptance empty) plus records: an `opened` record; one `review`
      record per matching v1 review file (mapping verdict, findings,
      reviewer role/vendor/model/email); a `completed` record when v1
      `Status: done` (completed_commit from `Merged-Commit`, else
      `Reviewed-Commit`); an `abandoned` record when `Status: abandoned`
      (reason from the header if present, else a fixed
      "migrated from v1" reason).
- [ ] The tool prints a per-task summary and a final count; it exits
      non-zero if any task or review fails to parse or if a migrated
      task fails to re-project (fail-closed), naming the offending file.
- [ ] Migrated records pass the existing v2 validators; a migrated
      task's projected state via `load_task_status` equals its v1
      `Status` (open->open, in_review->open, done->done,
      abandoned->abandoned).
- [ ] The target directory must not already contain a journal (refuse to
      overwrite); the source is never modified (verified by tests).
- [ ] A malformed v1 task header, an unknown `Status`, a review whose
      verdict/findings are inconsistent, or a review referencing an
      unknown task are fail-closed errors, not silent skips.
- [ ] Tests cover, with fixtures mirroring the real v1 format: a done
      task with an approved review; an abandoned task; an open task with
      a changes_required review; the state-equivalence check; refusal on
      a non-empty target; non-mutation of the source; each fail-closed
      case.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check`, `mypy` green
      locally and in CI on the reviewed SHA.

## Non-Goals

- No stats -> session-record migration (measurement channel is CR-019);
  no in-place mutation; no provider/CI wiring (CR-017); no automatic
  cutover (operator-run during the self-hosting milestone).
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
