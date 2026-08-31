+++
schema = 1
id = "CR-068"
title = "Prune the worktrees of finished tasks, not only their branches"
scope = ["src/agentmarshal/journal/prune.py", "src/agentmarshal/cli.py", "tests/test_prune.py", "docs/quickstart.md"]
acceptance = [
  "the command is `agentmarshal prune`, and it reports both branches and worktrees of finished tasks",
  "a worktree is eligible only when its checked-out branch names a task the journal projects as done and the worktree has no uncommitted changes",
  "the main worktree is never eligible",
  "`--delete` removes an eligible worktree without forcing, and reports a refusal instead of overriding it",
  "a worktree whose task is open, abandoned or unknown is skipped, and the report says which",
  "branch pruning keeps the behaviour CR-059 established, including that a branch held by a worktree is never eligible",
  "no remote is contacted in either mode",
]
+++

# CR-068: Prune the worktrees of finished tasks, not only their branches

## Context

Adopter proposal 010. The audit that prompted it found **45 executor worktrees**
alongside 46 local branches, accumulated outside the journal and outside any
gate. CR-059 answered the branches; the worktrees are the larger half of the
same count, and the reporter's point was that nothing says which task an
artifact belonged to or when it may go.

The journal answers both questions for a worktree exactly as it does for a
branch: the branch checked out in it names a task, and the task's projected
state says whether the work is finished.

**The command is renamed from `prune-branches` to `prune`.** It has never been
released — it landed after 0.1.0 — so the name can still be corrected, and a
command that removes worktrees should not be called after branches. Renaming
after publication would be a cost paid by every adopter; renaming now costs
nothing.

## Objective

Report and remove the worktrees of finished tasks under the same two conditions
that govern branches, and give the command a name that covers what it does.

## Acceptance Criteria

- The command is `agentmarshal prune`. It reports branches **and** worktrees.
- A worktree is eligible only when both hold: the branch checked out in it names
  a task the journal projects as `done`, and the worktree has no uncommitted
  changes.
- The main worktree is never eligible.
- `--delete` removes an eligible worktree **without forcing**, and reports a
  refusal from git rather than overriding it.
- A worktree whose task is open, abandoned or unknown to the journal is skipped,
  and the report states which of those it was.
- Branch pruning keeps every behaviour CR-059 established, including that a
  branch held by a worktree is never eligible and that deletion does not force.
- Neither mode contacts a remote.

## Threat model and boundaries

This command destroys things, so the hazard is real and is the same one CR-059
named: **irreversible loss of the operator's own work**, not an attacker. A
worktree is worse than a branch in one respect — it can hold *uncommitted*
changes, which exist nowhere else at all.

That is why a worktree carries an extra condition its branch does not: it must
be clean. And why removal must not force: `git worktree remove` refuses a dirty
or locked worktree, and that refusal is a second, independent opinion about
whether the operator is about to lose something. Overriding it would leave our
own check as the only thing standing between them and the loss — the mistake
CR-059 already corrected once for branches.

Remotes stay out of reach by construction, not by a check, as in CR-059. That is
also why proposal 010's warning about backup mirrors needs no guard here.

Not defects in this task, and not to be guarded against: symlinks or path
traversal on a worktree path — the paths come from `git worktree list` in the
operator's own repository; a hostile branch or worktree name, for the same
reason; concurrent git operations, where git's own locking is the answer.

## Non-Goals

- Removing any other executor artifact — scratch checkouts, stash entries,
  temporary clones. The journal can say nothing about an artifact whose name
  does not carry a task id.
- Recording pruning in the journal. This command reads evidence; it writes none.
- Running automatically from any other command.
- A repo-level policy about which remote is the working one. That is guidance,
  and it belongs in the documentation rather than in a command that never
  contacts a remote.
