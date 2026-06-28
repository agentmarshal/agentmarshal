# Методология AgentMarshal

Document-ID: agentmarshal-methodology
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

Методология AgentMarshal описывает, как команда AI-агентов работает в Git без
потери audit trail: роли, профили, коммуникация, review, triage и trial runs.

<!-- Section-ID: documents -->
## Документы

- [parallel-work.md](parallel-work.md) — worktree-per-agent и scope isolation.
- [agent-comms.md](agent-comms.md) — durable journal и artifact protocol.
- [execution-profiles.md](execution-profiles.md) — tools/write/network policy.
- [vendor-adapters.md](vendor-adapters.md) — role spec to vendor adapter.
- [review-triage.md](review-triage.md) — findings, debt bundles, risk.
- [trial-agents.md](trial-agents.md) — testing models and roles.

<!-- Section-ID: workflow -->
## Workflow

Обычный поток:

```text
task contract → scoped branch/worktree → tests → pipeline → read-only review
→ merge policy → post-merge completion → stats/evidence
```

Для cutoff tasks поток упаковывается в AgMake runbook.

<!-- Section-ID: roles -->
## Roles

Role задаёт ownership и scope. Execution profile задаёт фактический runtime:
tools, write policy, network policy, session persistence и recorder. Role и
profile не должны смешиваться.

<!-- Section-ID: reviews -->
## Reviews

Reviewer проверяет чужой exact SHA, пишет blocking и non-blocking findings со
stable IDs и не материализует canonical tasks в read-only profile. Approved
follow-ups проходят через trusted recorder.
