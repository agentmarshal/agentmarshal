# CR-010: metadata-free review snapshot, contract bound to the commit

Owner: lead
Type: fix
Priority: P1
Created: 2026-07-19
Status: in_review
Scope:
- .agentmarshal/journal/tasks/open/CR-010-restore-archive-snapshot.md
- src/agentmarshal/
- tests/

## Context

CR-009 merged a working review launcher, but its final iteration
reinstated a detached-worktree snapshot, losing the metadata-free
property decided during that task: a worktree's `.git` file points into
the primary repository's metadata, so the launcher exposes a writable
path it does not need to expose. The reviewer-side finding that caused
the reinstatement was itself correct — the contract must come from the
reviewed commit, not the working tree — and must be preserved.

This task reinstates the lead decision (ADR-0001: process isolation
belongs to the vendor sandbox; the launcher's own guarantee is a
snapshot that exposes nothing) while keeping the contract-at-commit
property. Implemented by the lead.

Design constraints (binding):

- Snapshot = `git archive --format=tar <commit>` extracted with stdlib
  `tarfile` (`filter="data"`); no `.git` entry exists in the snapshot;
  an empty tree (a lone `pax_global_header` tarfile rejects) yields an
  empty snapshot, verified via `git ls-tree`.
- The task contract text given to the reviewer is read from the
  extracted snapshot (`.agentmarshal/journal/tasks/<id>/contract.md`
  inside it), never from the working tree; a commit that does not
  contain the contract is a fail-closed error.
- No worktree machinery remains: no registration, no prune paths;
  cleanup is the temporary directory's own removal.
- Standard library only; existing recording/validation paths unchanged.

## Objective

The review snapshot contains no repository metadata, the reviewer's
contract comes from the reviewed commit, and the worktree machinery is
gone.

## Acceptance Criteria

- [ ] `launch_review` materializes the snapshot via `git archive` +
      stdlib tar extraction as specified; no `git worktree` invocation
      remains in the launcher; `_remove_snapshot` and its recovery
      paths are removed.
- [ ] The reviewer prompt's contract section is read from the extracted
      snapshot; reviewing a commit whose tree lacks the task's contract
      is a clear fail-closed error with nothing recorded.
- [ ] An uncommitted working-tree change to the contract does not
      appear in the reviewer prompt (existing test preserved).
- [ ] A probing stub reviewer confirms the snapshot exposes no `.git`
      entry and that a file written into the snapshot does not appear
      in the repository; no `agentmarshal-review-*` directory survives
      a run; `git worktree list` stays single-entry throughout.
- [ ] The empty-tree edge case yields an empty snapshot and a clear
      fail-closed error for the missing contract, not a tar parsing
      error.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No changes to the verdict protocol, adapters, recording or
  projections.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
