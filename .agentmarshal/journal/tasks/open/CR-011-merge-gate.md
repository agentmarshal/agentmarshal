# CR-011: the merge gate

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: open
Scope:
- .agentmarshal/journal/tasks/open/CR-011-merge-gate.md
- src/agentmarshal/
- tests/

## Context

The gate is where the product's promise is enforced: a change merges
only with an approved independent review bound to its exact commit, a
pipeline attestation, and a diff inside the contract's scope
(ADR-0001; ADR-0003 for scope; ADR-0004 for reading state from
records). Journal-only transactions ride a cheap deterministic lane.
Implemented by the lead (gate code follows the v1 discipline of not
being written by managed workers).

Design constraints (binding):

- All journal reads via existing loaders; git via the established
  `subprocess.run(["git", ...])` pattern; standard library only.
- Fail-closed everywhere: any unreadable or inconsistent input is a
  refusal with a reason, never a pass.
- Independence needs a comparable identity: the review record's
  `reviewer` object gains a required `email` field (schema stays 1 —
  no review records exist yet in any real v2 journal). The launcher
  and `submit-review` accept `--email`; the gate compares it against
  the author and committer emails of every commit in the candidate
  range.

## Objective

`agentmarshal gate` verifies a merge candidate and reports pass or a
list of violations.

## Acceptance Criteria

- [ ] `agentmarshal gate --task CR-NNN --commit <sha> --base <ref>`
      resolves the candidate range as `merge-base(base, commit)..commit`
      and checks, printing one line per check and exiting non-zero on
      any violation:
      1. the task exists with an `opened` record and is not closed;
      2. **scope**: every path changed in the range is covered by the
         contract's `scope` list (a scope entry ending in `/` covers
         the subtree; otherwise exact match);
      3. **review**: the latest review record for exactly `<sha>` has
         verdict `approved`;
      4. **independence**: that review's `reviewer.email` is non-empty
         and differs from every author and committer email in the
         range;
      5. **pipeline**: `<sha>` equals the attestation passed via
         `--pipeline-sha` or `AGENTMARSHAL_PIPELINE_OK_SHA`;
      6. **record collision**: no file added in the range under a
         `records/` directory already exists in the base tree.
- [ ] **Journal-only lane**: when every changed path is under
      `.agentmarshal/journal/`, checks 2–4 are skipped and reported as
      the deterministic lane; pipeline and record-collision checks
      still apply.
- [ ] The `review` record's `reviewer` object requires `email`
      (non-empty, contains `@`); `submit-review` and `review` CLI
      verbs accept `--email`; existing consistency rules unchanged.
- [ ] Tests cover: a passing candidate end-to-end (open →
      committed change → approved review with independent email →
      gate passes with attestation); each violation separately (path
      outside scope; no review for the SHA; latest review not
      approved; reviewer email matching an author and a committer;
      missing attestation; wrong attestation SHA; record-path
      collision); the journal-only lane passing without any review;
      a task without an `opened` record.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No provider/MR integration, no CI job wiring, no completion writing
  (next slice), no v1-gate changes, no enforcement replacement for
  this repository's own governance yet (that is the self-hosting
  milestone).
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
