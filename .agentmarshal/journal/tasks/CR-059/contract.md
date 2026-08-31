+++
schema = 1
id = "CR-059"
title = "Report and delete local branches of tasks the journal says are done"
scope = ["src/agentmarshal/journal/prune.py", "src/agentmarshal/cli.py", "tests/test_prune.py"]
acceptance = [
  "`agentmarshal prune-branches` lists local branches eligible for deletion and deletes nothing",
  "a branch is eligible only when its name names a task the journal projects as done AND it is fully merged into the base ref",
  "`--delete` attempts to delete exactly the branches the report listed, and reports any that git itself refuses rather than forcing them",
  "the branch currently checked out is never eligible, even when it satisfies every other condition",
  "a branch whose task is open, abandoned, or unknown to the journal is never eligible, and the report says why it was skipped",
  "no remote is contacted and no remote ref is deleted by either mode",
  "`--base <ref>` selects the ref merged-ness is judged against, defaulting to the current HEAD",
]
+++

# CR-059: Report and delete local branches of tasks the journal says are done

## Context

Adopter proposal 010. An audit on the reporter's repository found **45 executor
worktrees and 46 local branches** accumulated outside the journal and outside
any gate: nothing in the model says when such an artifact may be removed, or
which task it belonged to.

It converges with a gap we had already recorded on ourselves. AgentMarshal
creates at least two branches per task — implementation and completion — the
provider does not delete the source branch on merge, and merged task branches
accumulate. We have been pruning them by hand. At least one provider fails
closed once a repository passes roughly a hundred branches, which turns
untidiness into an outage.

The journal already knows which tasks are finished. That knowledge is what makes
a safe answer possible: a branch may be removed when the task it belongs to is
done and git confirms its commits are already contained in the base.

## Objective

A command that reports which local branches belong to finished tasks and are
fully merged, and deletes them only when explicitly asked.

## Acceptance Criteria

- `agentmarshal prune-branches` prints the eligible branches and **deletes
  nothing**.
- A branch is eligible only when both hold: its name contains a task id the
  journal projects as `done`, and git reports it fully merged into the base ref.
- `--delete` attempts to delete exactly the branches the report listed, naming
  each as it goes, and **reports** any that git itself refuses instead of
  forcing them through.
- The currently checked-out branch is never eligible.
- A branch whose task is `open`, `abandoned`, or absent from the journal is
  never eligible, and the report states which of those it was.
- Neither mode contacts a remote or deletes a remote ref.
- `--base <ref>` chooses the ref merged-ness is judged against; it defaults to
  the current `HEAD`.

## Threat model and boundaries

**Unlike most of this codebase, this command destroys things, so it has a real
hazard — and it is not a hostile contributor.** Everything here runs in the
operator's own checkout on their own branches. The hazard is *irreversible loss
of the operator's own work*: deleting a branch that still carries commits
nowhere else.

That hazard is addressed by two independent conditions that must both hold, and
by the default being a report:

- **git must confirm containment.** Merged-ness is decided by git against the
  base ref, not by a name convention, so a branch whose commits are not already
  in the base is never eligible however it is named.
- **the journal must confirm the task is finished.** A task still open is work
  in progress regardless of what git says about its commits.
- **the default mode deletes nothing**, so the destructive path is always a
  second, deliberate invocation.

Because these conditions are independent, the deletion itself must not discard
git's own. `git branch -D` removes a branch whether or not git considers it
merged, which would leave our containment check as the only thing standing
between the operator and lost work. The deletion uses `git branch -d` and
surfaces a refusal. A refusal is information — it means git and this command
disagree about containment, which is exactly the case the operator needs to see
rather than have overridden. It can happen legitimately: `-d` judges against
HEAD and its upstream, while `--base` may name another ref.

**Remotes are out of reach by construction, not by a check.** Proposal 010 warns
that cleanup must target the working remote only and never a backup mirror. This
command never contacts a remote at all, which removes that hazard rather than
guarding against it. That is why "never delete from a mirror" is an acceptance
criterion about what is *not* done rather than a safeguard to implement.

The following are **not** defects in this task and must not be guarded against:

- **Symlinks, path traversal or TOCTOU on the repository or journal path.** The
  repository is the operator's own checkout; this command reads it the way every
  other command in this tool does. The project has recorded an incident about
  this reflex — `docs/incidents/2026-08-31-scope-warning-scope-creep.md`.
- **A hostile branch name.** Branch names come from the operator's own
  repository. Refuse a name that does not parse; do not build a sanitizer.
- **Concurrent git operations.** If the operator runs git elsewhere at the same
  moment, git's own locking is the answer, not ours.

## Non-Goals

- **Deleting remote branches, worktrees, or any artifact other than a local
  branch.** Proposal 010's executor worktrees are a larger question and are not
  addressed here.
- **A repo-level operations policy** stating which remote is the working one.
  That is a separate document and a separate decision.
- **Accounting artifacts against the task that produced them** in the journal.
  This command reads the journal; it writes no record.
- **Running automatically** as part of `complete` or any other command.
