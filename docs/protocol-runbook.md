# Protocol runbook

Protocol runbook is a task-local executable plan for a human or external runner.
It turns an AgentMarshal workflow into a linear shell script with explicit
gates, bounded loops and debug handoff.

It is not a dispatcher, daemon, queue, model runtime or dashboard. AgentMarshal
core still provides policy, contracts and evidence checks; the runbook only
executes a prepared protocol for one task or one related task batch.

AgMake is the built-in reference layer for generating and checking these
runbooks. The detailed transactional section contract is described in
[`agmake.md`](agmake.md).

## Scope

A runbook belongs to a concrete task/batch and is generated after the model has
enough context to define exact commands. It should live in ignored runtime
state, for example:

```text
.agents/tmp/runner/CR-NNN-runbook.sh
```

Tracked documentation and templates may live in `agentmarshal/docs/` and
`agentmarshal/templates/`, but concrete runbooks are not committed. They contain
local MR IDs, timestamps, logs, retry state and operator-specific context.

## Relationship to external runner contract

The external runner contract defines what facts and artifacts a runner must
produce. A protocol runbook is one possible manual implementation of that
contract:

- it receives fixed task/SHA/branch/provider values;
- it runs only allowlisted project commands;
- it waits and polls outside the model session;
- it writes logs and prints exact artifacts;
- it stops on unknown state and prints a debug handoff.

The model should prepare the runbook, then stop. The operator runs it in a
terminal. The model returns only after success summary or failure handoff.

## Required Sections

Each runbook should print named protocol sections:

```text
00 preflight
10 push and MR
20 pipeline
30 review loop
40 merge policy
50 merge
60 completion transaction
70 completion pipeline
80 completion review
90 completion merge
99 summary
```

Not every task needs every section, but skipped sections must be explicit.

## Review loop

Review is the only required loop in v0.1 runbooks. It must be bounded:

```text
max_review_loops=3
```

For each review attempt the runbook must:

- run the configured read-only review command for exact SHA;
- locate the produced artifact;
- inspect `Reviewed-Commit` and `Verdict`;
- continue only on `Verdict: approved`;
- fail on `changes_required`, unknown verdict, stale SHA or missing artifact.

The runbook must not edit code in response to review. Fixes require a new model
session and a new runbook/commit.

## Pipeline polling

Pipeline polling is allowed inside a runbook because it runs in a terminal
process, not in a model session. Polling must be tied to exact commit SHA and
must fail closed on:

- missing pipeline;
- failed/warning/cancelled terminal state;
- timeout;
- provider/API transport error after configured retries.

## Resume and re-entry

Runbooks should support explicit resume for long workflows:

```bash
RUNBOOK_FROM=30 bash .agents/tmp/runner/CR-NNN-runbook.sh
```

`RUNBOOK_FROM` is a section number. Earlier sections are skipped after loading
checkpoint state from:

```text
.agents/runs/runner/CR-NNN/state.env
```

The state file should contain only non-secret execution facts such as:

- implementation SHA;
- implementation MR ID;
- pipeline IDs;
- review artifact paths;
- completion branch;
- completion SHA;
- completion MR ID.

Operator-provided environment values, for example `MR_ID=90`, may be used when a
failure happened before the state file was written. Sections that are not safely
reentrant must document their requirements and fail with a debug handoff instead
of guessing.

## Evidence placement

Implementation branches should not receive tracked runner events after review,
because any tracked change changes the reviewed SHA. Use these placements:

| Artifact | Location | Tracked |
|---|---|---|
| concrete runbook | `.agents/tmp/runner/` | no |
| runbook stdout/log | `.agents/runs/runner/` | no |
| raw review output | `.agents/runs/` | no |
| canonical completion review | `.agents/reviews/YYYY/` | yes |
| durable runner event | `.agents/events/YYYY/CR-NNN/` | yes, usually completion branch |
| task done move | `.agents/tasks/done/YYYY/` | yes, completion branch |

## Debug handoff

On failure, the runbook should print a compact block that can be pasted into a
model session:

```text
AGENTMARSHAL_RUNBOOK_FAILURE
Task: CR-NNN
Section: 30 review loop
Branch: ...
SHA: ...
MR: ...
Pipeline: ...
Review-File: ...
Log: ...
Reason: ...
Next-Hint: ...
```

The handoff should identify state and artifacts, not ask the operator to
interpret stack traces.

## Non-goals

- No generic command execution.
- No background scheduler.
- No service supervision.
- No automatic code fixing after review.
- No bypass of merge-policy, scope-guard, review or pipeline gates.
- No required Python runtime for v0.1.

## Minimal Command

A generated runbook should be directly executable:

```bash
bash .agents/tmp/runner/CR-NNN-runbook.sh
```

If a task needs operator-provided values, prefer named environment variables
with explicit preflight errors over interactive prompts.
