# agentmarshal methodology

Методики организации параллельной работы команды агентов. Архитектура и public
host contract описаны в [`../docs/`](../docs/README.md).

## Документы

| Док | О чём |
|---|---|
| [parallel-work.md](parallel-work.md) | worktree-per-agent, уровни изоляции (engineering vs security), sparse-checkout |
| [agent-comms.md](agent-comms.md) | журнал `.agents/`, артефактный протокол, шаблоны task/ADR/handoff/review |
| [vendor-adapters.md](vendor-adapters.md) | agnostic role-спек → нативный конфиг вендора; multi-vendor из коробки |
| [execution-profiles.md](execution-profiles.md) | воспроизводимые tools/write/network/session ограничения запуска |
| [gitflic-control-plane.md](gitflic-control-plane.md) | проверенный GitFlic API, pipeline/job transport и runner fallback |
| [review-triage.md](review-triage.md) | blocking/follow-up/accepted-risk policy и автоматический recorder |
| [trial-agents.md](trial-agents.md) | cross-review, operational/controlled trials, scoring и рейтинг |

## Как использовать

1. [parallel-work.md](parallel-work.md) определяет workspace/branch topology.
2. [agent-comms.md](agent-comms.md) задаёт durable artifact protocol.
3. [execution-profiles.md](execution-profiles.md) ограничивает runtime tools.
4. [vendor-adapters.md](vendor-adapters.md) связывает policy с конкретным CLI.
5. [trial-agents.md](trial-agents.md) проверяет новую модель/роль до активации.
6. [review-triage.md](review-triage.md) не даёт approved findings потеряться.
7. Provider transport документируется отдельно, например
   [gitflic-control-plane.md](gitflic-control-plane.md).
