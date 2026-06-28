# Контракт AgentMarshal с host repository

## Роли сторон

AgentMarshal предоставляет:

- schemas, validators и methodology;
- role/profile model;
- enforcement scripts;
- vendor/provider adapters;
- recorder и test fixtures.

Host repository предоставляет:

- project root и Git history;
- project config и journal в настраиваемых host paths;
- role ownership paths и prompts;
- provider credentials/configuration;
- CI wiring;
- MR/merge integration;
- secrets policy;
- human gates.

## Целевая файловая структура

После extraction:

```text
host/
  agentmarshal/                 # submodule, pinned exact commit
  .agentmarshal/
    project.json            # stable bootstrap anchor
    config/runtime.conf     # operator-editable runtime config
    agents/                 # host role specs
    prompts/                # project context
    providers/              # GitFlic/GitHub/GitLab binding
    journal/
      stats/                # tracked normalized metrics
      tasks/ events/ ...    # host journal
      runs/ tmp/            # ignored
  .gitmodules
  <host CI config>
```

Framework не должен требовать, чтобы host назывался `agentmarshal-host`, default
branch был `master` или Git provider был GitFlic.

## Уровни host configuration

`.agentmarshal/project.json` является стабильным bootstrap-anchor и безопасным
JSON data file. Он указывает paths к runtime config, journal, role specs,
prompts, plugin roots и provider binding.

`.agentmarshal/config/runtime.conf` содержит часто меняемые runtime-параметры:
язык review, active roles, worktree root/pattern и stats policy. Это безопасный
`key=value` data file, не shell script.

Все пути, кроме стандартного anchor, настраиваемы. Текущий `.agents/` layout
является legacy и может быть записан в `project.json` как custom journal path
на период миграции.

## Обязательный discovery interface

Целевой запуск:

```bash
AGENTMARSHAL_PROJECT_ROOT=/path/to/host
AGENTMARSHAL_PROJECT_CONFIG=/path/to/host/.agentmarshal/project.json \
  /path/to/host/agentmarshal/scripts/validate.sh
```

Discovery priority:

1. явный CLI option;
2. environment variable;
3. `.agentmarshal/project.json` от project root;
4. legacy `.agents/` fallback на ограниченное compatibility window;
5. fail closed с понятной ошибкой.

Policy binding groups:

```text
repository:
  name, default branch, remote
roles:
  spec directory, role email map
provider:
  default provider, declared secret bindings
integration:
  MR command, CI policy command
```

Production hosts/domains не являются обязательной частью generic AgentMarshal и
должны находиться в optional host extension.

## Journal contract

По умолчанию host создаёт:

```text
.agentmarshal/journal/tasks/open/
.agentmarshal/journal/tasks/done/YYYY/
.agentmarshal/journal/tasks/abandoned/YYYY/
.agentmarshal/journal/events/YYYY/
.agentmarshal/journal/handoffs/YYYY/
.agentmarshal/journal/reviews/YYYY/
.agentmarshal/journal/decisions/
.agentmarshal/journal/stats/runs/YYYY/
.agentmarshal/journal/runs/       # ignored
.agentmarshal/journal/tmp/        # ignored
```

Framework ADR не копируются в host journal decisions. Этот каталог предназначен
для решений host-проекта: архитектура приложения, tenant policy, deployment,
project-specific exceptions.

Normalized stats являются частью record plane. Raw model/session metrics
остаются в configured ignored runs directory.

## Bootstrap contract

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init
./agentmarshal/bin/agentmarshal init
./agentmarshal/bin/agentmarshal doctor
```

`init` обязан поддерживать interactive/non-interactive режимы, `--dry-run` и
`--adopt-existing`; не перезаписывать существующие файлы без согласия и
завершаться validation. Existing `.agents/` получает move/keep/abort migration.

## CI contract

Host CI обязан:

1. checkout pinned AgentMarshal submodule;
2. не обновлять submodule до remote HEAD;
3. установить runtime dependencies scripts;
4. запустить trusted scope gate до тяжёлых jobs;
5. запустить `validate.sh`;
6. запустить AgentMarshal tests, если изменён framework/binding/journal;
7. сохранить exact commit SHA pipeline.

Пример:

```yaml
script:
  - git submodule update --init --recursive
  - apk add --no-cache bash git jq
  - bash agentmarshal/scripts/validate.sh
  - bash agentmarshal/tests/negative.sh
```

После extraction AgentMarshal repository имеет собственный CI. Host CI проверяет
интеграцию pinned release, а framework CI — standalone behavior.

## Git hook contract

Pre-push hook принадлежит host repository. Он может вызывать AgentMarshal:

```bash
bash "$HOST_ROOT/agentmarshal/scripts/scope-guard.sh" \
  --repo "$HOST_ROOT" \
  --agents-dir "$HOST_ROOT/.agentmarshal/agents" \
  --branch "$remote_ref" \
  --head "$local_sha" \
  --base "origin/$default_branch"
```

Hook не является единственным gate: пользователь может обойти local hooks,
поэтому CI повторяет проверку.

## Provider adapters

Provider-specific операции должны быть за adapter boundary:

```text
resolve branch SHA
list/inspect pipelines
list/inspect jobs
read MR metadata
create/merge/close MR
download immutable blobs
compare refs
```

Сейчас GitFlic transport распределён между `gitflic-ci.sh`,
`scope-guard-gitflic.sh`, `merge-policy.sh` и host `mr.sh`. До extraction он
переносится за versioned provider SPI. GitFlic является первым рабочим
adapter, mock обязателен для CI, GitHub/GitLab могут быть capability stubs.

`project.json` выбирает default provider:

```json
{
  "provider": {
    "default": "mock",
    "secret_bindings": {
      "GITFLIC_API_TOKEN": "AGENTMARSHAL_GITFLIC_API_TOKEN"
    }
  }
}
```

Fresh standalone bootstrap использует `mock`, чтобы `doctor` и CI не требовали
внешний Git provider. Host, которому нужен GitFlic, меняет default provider и
передаёт секреты через environment variables. `doctor` проверяет только наличие
объявленного env var или binding; значение секрета не печатается и не читается
из пользовательских credential files.

## Version compatibility

Host должен pin AgentMarshal exact commit или release tag. При обновлении:

1. прочитать AgentMarshal changelog;
2. обновить submodule в отдельной branch/task;
3. прогнать host integration tests;
4. обновить host config/schema;
5. получить review exact gitlink commit;
6. merge и зафиксировать mapping host commit → AgentMarshal commit.

Автоматическое слежение submodule за branch запрещено.
