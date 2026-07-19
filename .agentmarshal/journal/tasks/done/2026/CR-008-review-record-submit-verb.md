# CR-008: the review record and `agentmarshal submit-review`

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: done
Completion-Review: CR-008
Reviewed-Commit: 2754f5ec78fd48dae0256e0eddef490161d28951
Target-Branch: master
Merged-Commit: aa527d83ea29f1ac69387a06beb9137c595c11f3
Completed-At: 2026-07-19T05:32:29Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-008-completion-2754f5ec78fd.md
Completion-Review-SHA256: sha256:c319fdeb50e5672850e1a01b6687a1d00eee13338358f6de29656961ee2d3da6
Scope:
- .agentmarshal/journal/tasks/open/CR-008-review-record-submit-verb.md
- src/agentmarshal/
- tests/

## Context

The trusted review path is where trust is generated: a review verdict
must be recorded bound to the exact reviewed commit, with the reviewer's
identity, through a recorder that refuses inconsistent evidence
(ADR-0004 Decisions 3 and 4). This slice adds the `review` record type
and the verb that records it. Launching reviewers is a later slice; this
one is only the trusted recording path.

Design constraints (binding):

- Standard library only; `pathlib`; explicit `encoding=`; all journal
  I/O through the existing recorder/loader
  (`write_record`/`read_records`) — their validation and
  symlink-hardening guarantees are inherited, not reimplemented.
- Extend the record-type registry and the projection's explicit mapping;
  fail-closed everywhere.

## Objective

A validated `review` record type exists, `agentmarshal submit-review`
records verdicts, and `status` surfaces them.

## Acceptance Criteria

- [ ] Record type `review` with fields: `schema`, `record_type`,
      `task`, `created_at`, `tool_version`, `reviewed_commit` (exactly
      40 lowercase hex characters), `verdict` (one of `approved`,
      `changes_required`, `blocked`, `rejected`), `reviewer` (object
      with non-empty `role`, `vendor`, `model`), `findings` (array of
      unique non-empty finding-id strings). Validation is fail-closed
      and enforces internal consistency: `approved` requires an empty
      `findings` array; every other verdict requires at least one
      finding id. An inconsistent record is rejected on write and on
      load.
- [ ] `agentmarshal submit-review --task CR-NNN --commit <sha>
      --verdict <verdict> [--finding <id> ...] --role <r> --vendor <v>
      --model <m>` inside an initialized project: the task must exist
      and have an `opened` record; on success writes the review record
      and prints its path; on any violation (unknown task, malformed
      commit, inconsistent verdict/findings) — clear error, non-zero
      exit, nothing written.
- [ ] Projection: `review` records are an explicit no-transition rule
      (status stays as derived from lifecycle records);
      `agentmarshal status CR-NNN` lists each review as reviewed
      commit (short), verdict and finding count.
- [ ] Tests cover: a valid review round-trip (write, read back,
      shown in detail view); each consistency violation (approved with
      findings, changes_required without findings, bad commit length
      and non-hex, duplicate finding ids, empty reviewer field);
      unknown task; review against a task without an `opened` record;
      the listing still projects status correctly with review records
      present.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No reviewer launching, no vendor adapters, no gate logic, no
  independence checking (the gate's job, later slice), no prose review
  bodies — machine record only.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
