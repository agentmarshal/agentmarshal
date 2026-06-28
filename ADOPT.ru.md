# Подключение AgentMarshal

Document-ID: agentmarshal-adopt
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

AgentMarshal подключается к host repository как submodule. Framework-код живёт
в `agentmarshal/`, а конфигурация, journal и runtime state принадлежат host.

Цель подключения — получить проверяемые role/profile contracts, provider
binding, evidence journal, validation и AgMake runbooks без встраивания
project-specific policy в framework.

<!-- Section-ID: install -->
## Установка

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init --recursive
```

Host обязан pin exact AgentMarshal commit или release tag. Автоматическое
слежение submodule за branch запрещено.

<!-- Section-ID: init -->
## Инициализация

Новый проект:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language ru
```

Существующий проект с `.agents/`:

```bash
./agentmarshal/bin/agentmarshal init --adopt-existing --language ru
```

`init` создаёт `.agentmarshal/project.json`, runtime config, journal layout и
plugin roots. Fresh bootstrap использует mock provider, чтобы `doctor` не
требовал внешний Git provider.

<!-- Section-ID: configure -->
## Конфигурация

Оператор вручную редактирует:

- `.agentmarshal/project.json` — bootstrap anchor, paths, provider binding,
  plugin roots;
- `.agentmarshal/config/runtime.conf` или legacy `.agents/config/...` —
  `review_language`, active roles, worktree root, stats policy;
- host role specs, prompts и host-local plugins.

Секреты передаются через environment variables. AgentMarshal не читает
пользовательские credential files и не печатает secret values.

<!-- Section-ID: validate -->
## Проверка

```bash
./agentmarshal/bin/agentmarshal doctor
./agentmarshal/scripts/validate.sh
./agentmarshal/tests/bootstrap.sh
./agentmarshal/tests/provider-spi.sh
./agentmarshal/tests/resource-routing.sh
./agentmarshal/tests/negative.sh
```

Host CI должен запускать `validate.sh` и relevant AgentMarshal tests при
изменении framework, binding или journal.

<!-- Section-ID: next -->
## Дальше

После подключения:

1. Зафиксируй role ownership и execution profiles.
2. Настрой provider secrets и CI gates.
3. Запусти первый task через AgMake runbook.
4. Обновляй AgentMarshal submodule отдельной веткой с review exact gitlink.

Для fresh-host AgMake пишет runtime-артефакты под configured journal root,
обычно `.agentmarshal/journal/tmp/runner/`. Для adopted legacy host путь
остаётся под `.agents/tmp/runner/`.

Подробнее: [host integration](docs/host-integration.ru.md) и
[operations](docs/operations.ru.md).
