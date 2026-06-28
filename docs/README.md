# Документация AgentMarshal

Этот каталог является архитектурной и эксплуатационной документацией
**самого AgentMarshal**. Он должен сохранять смысл после extraction в отдельный
репозиторий и не зависеть от документации конкретного host-проекта.

## Карта документов

| Документ | Назначение |
|---|---|
| [architecture.md](architecture.md) | компоненты, trust boundaries, потоки данных и инварианты |
| [host-integration.md](host-integration.md) | контракт между AgentMarshal и подключающим репозиторием |
| [configuration-and-statistics.md](configuration-and-statistics.md) | runtime-параметры, worktrees и сбор метрик |
| [plugin-architecture.md](plugin-architecture.md) | plugin manifest, presets, trust и host extensions |
| [external-runner-contract.md](external-runner-contract.md) | контракт внешнего раннера и ручной coordinator mock |
| [protocol-runbook.md](protocol-runbook.md) | task-local executable runbook для manual/external runner |
| [agmake.md](agmake.md) | встроенный reference layer для transactional task-local runbooks |
| [cutoff-roadmap.md](cutoff-roadmap.md) | порядок работ и exit criteria до standalone v0.1 |
| [qualification-report.md](qualification-report.md) | sanitized v0.1 qualification report и evidence command |
| [operations.md](operations.md) | повседневные workflow Lead, worker, QA и recorder |
| [extraction-readiness.md](extraction-readiness.md) | критерии и план выделения AgentMarshal в отдельный репозиторий |
| [adr/README.md](adr/README.md) | архитектурные решения AgentMarshal |
| [incidents/README.md](incidents/README.md) | framework incidents и corrective controls |

Host runtime configuration и normalized statistics принадлежат host. Текущая
реализация использует `.agents/`; cutoff contract с configurable paths описан
в configuration-and-statistics, host integration и ADR-0007.

Методики выполнения работы находятся в [`../methodology/`](../methodology/).
Разделение намеренное:

- `docs/` объясняет устройство и публичный контракт фреймворка;
- `methodology/` описывает правила командной работы;
- `agents/` и `profiles/` содержат машиночитаемые policy;
- `scripts/` реализует enforcement и automation;
- host project config и journal принадлежат host; их paths не входят в
  framework repository.

## Источники истины

| Область | Источник истины |
|---|---|
| Архитектурные решения AgentMarshal | `agentmarshal/docs/adr/` |
| Архитектура и host contract | `agentmarshal/docs/` |
| Методика работы агентов | `agentmarshal/methodology/` |
| Role ownership и scope | host role specs, сейчас `agentmarshal/agents/*.yaml` |
| Execution capabilities | `agentmarshal/profiles/*.yaml` |
| Форматы машинных данных | `agentmarshal/schemas/` и `validate.sh` |
| Конкретные задачи/ревью/события | configured host journal |
| CI/MR transport конкретного host | host integration и provider scripts |

## Правило переносимости

Документ считается framework-документом, если он остаётся истинным после
замены:

- имени репозитория;
- Git provider;
- структуры исходников;
- production hosts/domains;
- набора ролей и моделей;
- CI-конфига host-проекта.

Если утверждение не проходит этот тест, оно относится к host configuration или
project journal и не должно становиться архитектурным решением AgentMarshal.
