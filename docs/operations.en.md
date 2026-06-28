# AgentMarshal Operations

Document-ID: agentmarshal-operations
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

AgentMarshal operations are built around Git, task contracts, CI, read-only
review and tracked evidence. An expensive model should not stay in a polling
loop: long waits are handled by a coordinator or an external runner.

<!-- Section-ID: lead-cycle -->
## Lead Cycle

1. Create or select a task contract.
2. Validate runtime config and journal.
3. Prepare a branch/worktree or a task-local AgMake runbook.
4. Wait for the exact implementation SHA.
5. Check the pipeline for that SHA.
6. Run independent review.
7. Merge through the policy gate.
8. Create the completion branch and close the task post-merge.

Basic checks:

```bash
agentmarshal/scripts/agentmarshal-config.sh show
agentmarshal/scripts/validate.sh
```

<!-- Section-ID: runner -->
## Runner

Until an automated runner exists, the coordinator manually executes the
external runner contract. Cutoff work uses AgMake:

```bash
agentmarshal/bin/agmake init --task CR-123 --branch docs/CR-123-example
agentmarshal/bin/agmake lint .agents/tmp/runner/CR-123-runbook.sh
bash .agents/tmp/runner/CR-123-runbook.sh
```

The runbook prints protocol sections, saves state/logs and emits a handoff
block for the model on failure.

<!-- Section-ID: review -->
## Review

Review is run only for an exact SHA:

```bash
agentmarshal/scripts/review-readonly.sh \
  --task CR-123 \
  --sha <full-sha> \
  --base origin/master \
  --vendor claude
```

An approved review must include `Reviewed-Commit`, `Verdict: approved` and
stable `Finding-IDs` when non-blocking findings exist.

<!-- Section-ID: completion -->
## Completion

A task is closed after the implementation branch has actually merged into the
target. The completion branch is created from the current target and contains
only the journal transaction:

```bash
agentmarshal/scripts/task-lifecycle.sh complete \
  --task CR-123 \
  --review-task CR-123 \
  --review-file .agents/runs/<review>.md \
  --reviewed-commit <full-sha> \
  --target-ref origin/master
```

The completion MR also passes pipeline, review and merge-policy.

<!-- Section-ID: stats -->
## Stats

Normalized statistics live in the configured `stats_store` (**tracked** by Git)
and are used to rank models/roles. Raw runs stay in `stats_raw_store`
(**ignored**, not Git-tracked). Tracked stats must not include secrets, private
prompts or full session transcripts.

Record a normalized stat manually:

```bash
agentmarshal/scripts/record-agent-stat.sh \
  --project-root /path/to/host \
  --task CR-123 --role <role> --vendor <vendor> --model <model> \
  --profile <profile> --activity <activity> --outcome <outcome> \
  --source-artifact manual
```

Summaries:

```bash
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host summary
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host ranking
```

`--project-root` is optional when running from the project root.
