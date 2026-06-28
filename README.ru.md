# AgentMarshal

Document-ID: agentmarshal-readme
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

AgentMarshal — маленькая инженерная система для governance/process-контура
поверх Git. Он помогает команде AI-агентов работать через проверяемые task
contracts, role/profile policy, review gates, provenance и evidence-журнал.

AgentMarshal не является model runtime, dispatcher, dashboard или памятью
агентов. Runtime может быть человеческим, CLI-based или внешним provider; ядро
фиксирует правила, артефакты и доверенные проверки.

<!-- Section-ID: quick-start -->
## Быстрый старт

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init --recursive
./agentmarshal/bin/agentmarshal init --preset minimal --language ru
./agentmarshal/bin/agentmarshal doctor --project-root .
./agentmarshal/bin/agentmarshal validate --project-root .
```

Для host с историческим archive `.agents`:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language ru \
  --legacy-archive .agents
```

Для task-local запуска протокола используется AgMake:

```bash
./agentmarshal/bin/agmake init --task CR-123 --branch docs/CR-123-example
./agentmarshal/bin/agmake lint .agentmarshal/journal/tmp/runner/CR-123-runbook.sh
bash .agentmarshal/journal/tmp/runner/CR-123-runbook.sh
```

<!-- Section-ID: contracts -->
## Контракты

Публичные контракты AgentMarshal:

- host integration: submodule, `.agentmarshal/project.json`, configurable
  journal и CI hooks;
- roles/profiles: ownership, allowed paths, tools, network/write policy;
- provider SPI: Git provider и CI/MR операции за adapter boundary;
- evidence plane: tasks, reviews, events, handoffs и normalized statistics;
- AgMake: deterministic task-local runbook, который исполняет протокол вне
  дорогой live model session.

Code identifiers, schemas, CLI flags и machine-readable data остаются
language-neutral.

<!-- Section-ID: docs-map -->
## Карта документации

- [Startup Guide](docs/startup-guide.ru.md)
- [Подключение](ADOPT.ru.md)
- [Операции](docs/operations.ru.md)
- [Host integration](docs/host-integration.ru.md)
- [Host adapter boundary](docs/host-adapter-boundary.ru.md)
- [Готовность к публичному релизу](docs/public-release-readiness.ru.md)
- [Политика публичного репозитория](docs/public-repository-policy.ru.md)
- [Методология](methodology/README.ru.md)
- [Architecture](docs/architecture.md)
- [Plugin architecture](docs/plugin-architecture.md)
- [AgMake](docs/agmake.md)
- [ADR](docs/adr/README.md)

<!-- Section-ID: status -->
## Статус

Текущий milestone: private `v0.1`.

Публичный релиз требует sanitized documentation, generic English-first bundled
prompts, standalone CI и минимум две проверенные host integrations.
