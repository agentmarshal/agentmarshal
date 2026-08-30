# 010 — External-executor artifacts have no lifecycle

- **Reporter:** Adopter A · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

When work is delegated to an external executor, the artifacts it leaves behind —
worktrees, branches, scratch checkouts — belong to no task and are governed by
nothing. An audit on the reporter's repository found **45 executor worktrees and
46 local branches** accumulated outside the journal and outside any gate.

Nothing in the model says when such an artifact may be removed, or which task it
belonged to.

## Proposed

Account for executor artifacts against the task that produced them, so their
lifecycle ends when the task does.

## Disposition — accepted

Accepted, and it converges with a gap we had already recorded: AgentMarshal
creates at least two branches per task (implementation and completion), the
provider does not delete the source branch on merge, and merged task branches
accumulate. We have been pruning them by hand.

Two related pieces of work fall out and both are ours: a helper that prunes
merged task branches, and a repo-level operations policy — cleanup must target
the working remote only, never a backup mirror, and at least one provider
fails closed once a repository passes roughly a hundred branches, which turns
untidiness into an outage. The executor case generalises both.
