# CR-017: gate context derivation (thin invocation wrapper)

Owner: lead
Type: feat
Priority: P2
Created: 2026-07-26
Status: in_review
Scope:
- .agentmarshal/journal/tasks/open/CR-017-gate-context-derivation.md
- src/agentmarshal/
- tests/

## Context

Self-hosting uses the vendor-neutral, invoked-at-merge enforcement model
(operator/skill runs `agentmarshal gate` at merge; decision 2026-07-26).
The gate CLI already works with explicit `--task/--commit/--base/
--pipeline-sha`. This slice removes the friction of that invocation by
letting the gate derive its context from the current git state, so the
operator (and later the "finish task" lifecycle skill) invokes it with
near-zero arguments. No change to what the gate checks or how it
enforces — only how its inputs are obtained. Gate-adjacent; keep it
small and fail-closed.

Design constraints (binding):

- Standard library only; the only external process is `git`; reuse the
  gate's existing `run_gate`, `_run_git`, `_resolve_commit` — do not
  duplicate git handling or any check.
- Task id derived from the current branch name via the branch policy
  encoding `<class>/CR-NNN-slug` (classes: feat, fix, docs, ci,
  completion); fail closed if the branch does not encode a task.
- Fail-closed on a detached HEAD, an unborn branch, or a branch whose
  name carries no `CR-NNN`.

## Objective

`agentmarshal gate` can derive task, commit and base from the current
git context, reducing invocation to at most a base override.

## Acceptance Criteria

- [ ] On the `gate` command, `--task` and `--commit` become optional:
      when `--task` is omitted it is derived from the current branch
      name (`CR-NNN` extracted from `<class>/CR-NNN-slug`); when
      `--commit` is omitted it is the current `HEAD`. `--base` remains,
      defaulting to the repository's default branch (detected via
      `origin/HEAD`, falling back to `master`). `--pipeline-sha` keeps
      its current env fallback.
- [ ] Explicit flags still work and override derivation; the gate's
      checks and output are unchanged.
- [ ] Fail-closed with a clear message (non-zero, nothing gated) when:
      the branch name encodes no `CR-NNN` and `--task` is not given;
      HEAD is detached or unborn and `--commit` is not given; the
      default branch cannot be resolved and `--base` is not given.
- [ ] A derivation helper (branch→task, resolve HEAD, resolve default
      base) is unit-testable independently of the full gate.
- [ ] Tests cover: derivation on a `feat/CR-001-...` branch produces
      task CR-001 and HEAD commit; explicit flags override derivation;
      each fail-closed case; a full derived-context gate pass on a
      prepared repo (open task, in-scope change, approved independent
      review, attestation) equals the result of the explicit invocation.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check`, `mypy` green
      locally and in CI on the reviewed SHA.

## Non-Goals

- No CI-job mode, no provider/MR API integration, no branch-protection
  config (that is the rejected Variant 2). No change to any gate check
  or to `gitflic-ci.yaml`. No lifecycle skill yet (CR-018).
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
