# CR-009: the read-only review launcher

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: done
Completion-Review: CR-009
Reviewed-Commit: 7890096144269b91e6261f6e5b33159e5fbdeae7
Target-Branch: master
Merged-Commit: 6a82a4860455aca5124e4d2d44e5b5f8befb376a
Completed-At: 2026-07-19T07:02:59Z
Completion-Review-Artifact: .agentmarshal/journal/reviews/2026/CR-009-completion-789009614426.md
Completion-Review-SHA256: sha256:b3e752b688c74f5d831c5b01296d454849dfda1c86efc980f3b67e71ee935cb5
Scope:
- .agentmarshal/journal/tasks/open/CR-009-review-launcher.md
- src/agentmarshal/
- tests/

## Context

CR-008 delivered the trusted recording path; this slice delivers the
launching half of the trusted review path (ADR-0001): prepare an
exact-SHA snapshot, run a reviewer, validate its machine verdict and
record it through the CR-008 recorder. Conceptually this mirrors the v1
launcher (`agentmarshal/scripts/review-readonly.sh` in the archived
submodule) rebuilt on the v2 journal model.

Design constraints (binding):

- **Subprocess policy, amended for the adapter layer**: core logic
  still invokes only `git`; the vendor-adapter layer additionally may
  invoke the reviewer CLI as a subprocess. This exception is explicit
  and confined to the adapter boundary.
- Snapshot: `git worktree add --detach <tempdir> <sha>` outside the
  working tree; the reviewer runs with the snapshot as its working
  directory; the worktree is always removed afterwards
  (`git worktree remove --force`), including on every failure path.
- Reviewer machine-verdict protocol: the assembled prompt instructs the
  reviewer to print exactly one JSON object between sentinel lines
  `AGENTMARSHAL_VERDICT_BEGIN` and `AGENTMARSHAL_VERDICT_END`, with
  fields `reviewed_commit`, `verdict`, `findings` (array of unique
  finding-id strings). Parsing is fail-closed; gates and the launcher
  never parse prose (ADR-0004 Decision 3).
- All recording via the existing `submit-review` machinery
  (`write_record` + review validation) — inherited, not reimplemented.
- Standard library only; `pathlib`; explicit `encoding=`.

## Objective

`agentmarshal review` runs a reviewer against an exact commit in a
read-only snapshot and records the validated verdict.

## Acceptance Criteria

- [ ] `agentmarshal review --task CR-NNN --commit <sha> --base <ref>
      --role <r> --vendor <v> --model <m>` inside an initialized
      project: verifies the task exists with an `opened` record and
      that `<sha>` resolves in the repository; creates the detached
      snapshot; assembles the reviewer prompt from a role preamble
      (embedded template), the task contract text and
      `git diff <merge-base(base, sha)>..<sha>`; invokes the reviewer
      adapter with the snapshot as cwd; parses the sentinel-framed JSON
      verdict; requires `reviewed_commit` to equal `<sha>` exactly;
      records the review through the CR-008 validation path; prints the
      record path; removes the snapshot worktree.
- [ ] Adapter resolution: the environment variable
      `AGENTMARSHAL_REVIEWER_CMD` (an argv template where `{model}` and
      `{prompt_file}` placeholders are substituted per element) selects
      the reviewer command; it is the documented test/ops seam. A
      built-in `codex` template ships as the default for that vendor
      and is not exercised by CI.
- [ ] Fail-closed behavior, each case leaving no record and no leftover
      worktree: unresolvable commit; unknown task; adapter exiting
      non-zero; missing sentinels; invalid JSON between sentinels;
      `reviewed_commit` mismatch; a verdict/findings combination the
      recorder rejects.
- [ ] Tests use stub reviewer executables (written by the tests
      themselves, selected via `AGENTMARSHAL_REVIEWER_CMD`) to cover:
      an approved verdict round-trip (record readable via
      `read_records`, listed in `status` detail); a changes_required
      verdict with findings; every failure case above; and that
      `git worktree list` shows no leftover snapshot after each run.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No reviewer-independence checks (the gate's job), no prose review
  bodies, no execution-input records (follow-up slice), no `claude`
  adapter, no retries or budgets, no live vendor invocation in tests.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
