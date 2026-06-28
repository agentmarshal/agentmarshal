# AgentMarshal Methodology

Document-ID: agentmarshal-methodology
Document-Version: 1
Language: en

<!-- Section-ID: overview -->
## Overview

AgentMarshal methodology describes how an AI-agent team works in Git without
losing the audit trail: roles, profiles, communication, review, triage and
trial runs.

<!-- Section-ID: documents -->
## Documents

- [parallel-work.md](parallel-work.md) — worktree-per-agent and scope isolation.
- [agent-comms.md](agent-comms.md) — durable journal and artifact protocol.
- [execution-profiles.md](execution-profiles.md) — tools/write/network policy.
- [vendor-adapters.md](vendor-adapters.md) — role spec to vendor adapter.
- [review-triage.md](review-triage.md) — findings, debt bundles, risk.
- [trial-agents.md](trial-agents.md) — testing models and roles.

<!-- Section-ID: workflow -->
## Workflow

Normal flow:

```text
task contract → scoped branch/worktree → tests → pipeline → read-only review
→ merge policy → post-merge completion → stats/evidence
```

For cutoff tasks the flow is packaged into an AgMake runbook.

<!-- Section-ID: roles -->
## Roles

Role defines ownership and scope. Execution profile defines the actual runtime:
tools, write policy, network policy, session persistence and recorder. Role and
profile must not be mixed.

<!-- Section-ID: reviews -->
## Reviews

The reviewer checks someone else's exact SHA, writes blocking and non-blocking
findings with stable IDs, and does not materialize canonical tasks in a
read-only profile. Approved follow-ups go through a trusted recorder.
