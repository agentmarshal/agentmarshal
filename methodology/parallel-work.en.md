---
Document-ID: agentmarshal-methodology-parallel-work
Document-Version: 3
---

# Parallel Work: worktree-per-agent and Isolation

## Model

A small engineering system with roles, contracts, and auto-gates — not "many
agents simultaneously poking around the repository". Each active role gets a
dedicated git worktree (`<repo>.<alias>`, branches `<prefix>/*`), its own git
identity, its own (narrowed) permissions. Coordination — through Lead and
artifacts (see agent-comms.md).

## Isolation Levels (from soft to hard)

1. **sparse-checkout** — the agent sees only its own folders. Convenient, but
   **not a security boundary** (`git show HEAD:src/backend/...` bypasses it).
2. **sparse + scope-guard (pre-push/CI) + Lead review** — practical protection
   against mistakes and discipline. **← our choice**
   ([ADR-0002](../docs/adr/ADR-0002-agent-isolation.md)).
3. **sandbox without `.git`** — real read prohibition, but git workflow is lost.
4. **separate repositories** — true repo-level permissions, expensive (CI/CD,
   contracts, release coordination).

Decision: **engineering isolation, not security**. Secrets must be kept outside
the Git tree/worktree. Hard levels (3–4) are introduced specifically for
untrusted agents, untrusted code, or repositories with sensitive data.

## Mechanics

- Create/update worktree: `config/worktree/new-agent-worktree.sh <role> [slug]`
  (role identity + dev `.env` + narrowed permissions from template).
- Before launch, `scripts/worktree-lifecycle.sh worktree-preflight` verifies
  that the directory is registered by `git worktree`, shares the project Git
  common-dir, and can write shared metadata. A standalone clone is not an
  allowed fallback.
- Before a task — opening ritual: `scripts/persona-status.sh <worktree>`
  (branch, behind/ahead, clean, .env, identity). Codex lesson: a new task must
  not start from a stale world (FE-standby was 100+ commits behind).
- Boundaries are mechanically enforced by `scripts/scope-guard.sh`: `git diff`
  of branch ⊆ `scope_allow` of role (source — `agents/<role>.yaml`). Built into
  pre-push + CI.
- `fe/standby` style: keep a standby branch, update with `git pull --ff-only
  origin master`, new task — `git switch -c fe/<task> origin/master`
  (NOT `git checkout master` inside worktree — master is taken by the main
  worktree).

## Finalization and Cleanup

Files appearing in the primary worktree do not prove integration. The required
evidence is an integration commit in Git history:

```bash
agentmarshal/scripts/worktree-lifecycle.sh finalize \
  --integration-sha <full-sha> \
  --integration-ref feat/<task> \
  --require-pushed
```

The gate requires:

- primary `HEAD` exactly equals the integration SHA;
- the primary worktree is clean;
- the integration ref points to the same SHA;
- with `--require-pushed`, upstream has no ahead/behind commits.

Before removing a worker worktree:

```bash
agentmarshal/scripts/worktree-lifecycle.sh cleanup-ready \
  --worktree <path> \
  --integration-sha <full-sha> \
  --require-pushed
git worktree remove <path>
```

Copying tracked files from a clone/worktree into the primary worktree is not
an integration mechanism. If shared `.git` is unavailable, the workflow stops.
Recovery uses bundle/fetch/cherry-pick/merge, followed by the finalization gate.

## Completing a Task after Merge

Worktree finalization proves that the integration history is intact, but it
does not prove delivery to the default branch. The task remains `in_review`
until merge.

After an approved review of the exact SHA and a successful pipeline:

```bash
AGENTMARSHAL_PIPELINE_OK_SHA=<reviewed-sha> \
  agentmarshal/scripts/merge-policy.sh \
    --mr <id> --task CR-NNN --review-file .agents/runs/<review>.md
```

After the actual merge, create a journal-only completion branch from the
updated target:

```bash
git fetch origin --prune
git switch -c completion/CR-NNN origin/master

agentmarshal/scripts/task-lifecycle.sh complete \
  --task CR-NNN \
  --review-task CR-NNN \
  --review-file .agents/runs/<review>.md \
  --reviewed-commit <reviewed-sha> \
  --target-ref origin/master
```

Only this command moves the task to `done`, promotes the review to the
canonical journal, and records merge evidence. The completion branch passes
pipeline/review and is merged into the protected target through an MR. Its
diff is limited to journal artifacts; direct push to the target is not used.
`task-lifecycle.sh audit` revalidates every completed task.

## When to Parallelize

In parallel — independent tasks without a common sync point (FE screen + BE
feature based on a ready contract). Sequentially — when the second depends on
an artifact from the first (FE waits for API contract from BE). Sync point is
fixed by task/event/handoff.
