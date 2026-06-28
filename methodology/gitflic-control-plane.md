# GitFlic control plane для AgentMarshal

Проверенный read-only контракт GitFlic API для диспетчеризации агентов,
контроля CI и сбора evidence. Проектные значения owner/project/API задаются в
`agentmarshal.config.sh`, токен хранится вне репозитория.

Статус наблюдений: **эмпирически проверено 2026-06-22** на gitflic.ru и
self-hosted GitFlic Runner 4.10.0. Поведение API может меняться после обновления
GitFlic, поэтому transport покрывается mock-тестами, а неизвестные ответы
обрабатываются fail-closed.

## Готовые шлюзы

| Скрипт | Назначение |
|---|---|
| `agentmarshal/scripts/gitflic-ci.sh` | pipeline/job metadata, wait, диагностика |
| `infrastructure/scripts/mr.sh` | создание, список, merge и close MR |
| `agentmarshal/scripts/scope-guard-gitflic.sh` | trusted CI transport для scope guard |

Агентам не следует собирать одноразовые `curl`-команды, если операция уже есть
в этих шлюзах. Новая проверенная операция сначала добавляется в скрипт и тесты,
затем используется dispatcher'ом.

## Аутентификация

Для пользовательской автоматизации:

```text
Authorization: token <GITFLIC_API_TOKEN>
```

Токен читается из окружения или из
`~/.config/<project>/secrets.env` (`PROJECT_SECRETS_FILE` переопределяет путь).
Токены и полные HTTP-заголовки не сохраняются в `.agents/`.

В CI `scope-guard-gitflic.sh` сначала использует `CI_JOB_TOKEN` и пробует
совместимые с разными версиями runner/server заголовки. Для fallback допустим
masked read-only `AGENTMARSHAL_GITFLIC_API_TOKEN`.

## Проверенные endpoints

Все пути ниже относительны к:

```text
https://api.gitflic.ru/project/{owner}/{project}
```

| Endpoint | Результат / применение |
|---|---|
| `GET /` | metadata проекта и UUID |
| `GET /branch?size=100&page=N` | ветки и `lastCommit.hash` |
| `GET /branch/compare?compare=...&base=...` | changed files ветки |
| `GET /commit/{sha}` | commit metadata, parents, author |
| `GET /commit/{sha}/file` | файлы commit |
| `GET /blob/download?...` | содержимое файла по immutable SHA |
| `GET /blob/recursive?...` | дерево каталога |
| `GET /merge-request/list` | список MR |
| `GET /merge-request/{localId}` | MR, source/target branch и head SHA |
| `POST /merge-request` | создание MR |
| `POST /merge-request/{localId}/merge` | merge |
| `POST /merge-request/{localId}/close` | close |
| `GET /cicd/pipeline?size=100&page=N` | список pipeline |
| `GET /cicd/pipeline/{localId}/jobs?size=100&page=N` | jobs pipeline |
| `GET /cicd/job/{localId}` | metadata job и UUID |

## Существенные quirks

1. Проверенные query-фильтры pipeline `localId`, `ref` и `commitId`
   **игнорируются**. Нужно читать страницы списка и фильтровать точным
   сравнением на стороне клиента.
2. Pipeline идентифицируется локальным числовым ID в endpoint jobs:
   `/cicd/pipeline/{localId}/jobs`. Попытка получить pipeline как
   `/cicd/pipeline/{uuid}` давала 404.
3. Job metadata доступна по локальному ID. Проверенные sub-resources
   `/cicd/job/{id}/log` и `/trace` возвращали 404.
4. API token не является browser session для `gitflic.ru`; web UI может
   перенаправлять на login даже при валидном API token.
5. Через проверенные REST endpoints нельзя получить console stdout job.
   Это ограничение transport, а не отсутствие job metadata.

## CLI

```bash
# Последние pipelines
agentmarshal/scripts/gitflic-ci.sh list 10

# Точный pipeline и все jobs
agentmarshal/scripts/gitflic-ci.sh pipeline 189
agentmarshal/scripts/gitflic-ci.sh jobs 189
agentmarshal/scripts/gitflic-ci.sh diagnose 189

# Все pipeline точного commit SHA
agentmarshal/scripts/gitflic-ci.sh sha <full-40-char-sha>

# Polling: exit 0 только для SUCCESS; terminal failure != 0; timeout = 124
agentmarshal/scripts/gitflic-ci.sh wait 189 900 15

# Metadata конкретной job
agentmarshal/scripts/gitflic-ci.sh job 389
```

Команды, предназначенные для автоматизации, возвращают JSON. `diagnose`
возвращает короткий человекочитаемый список.

## Когда job упала

Диагностика идёт слоями:

1. `diagnose <pipeline>` находит упавшую job и её local ID.
2. `job <id>` даёт UUID job для корреляции с runner.
3. Для собственного WSL runner:

```bash
agentmarshal/scripts/gitflic-ci.sh runner-log <job-id>
```

По умолчанию используются WSL distro и container `gitflic-runner`. Override:
`AGENTMARSHAL_GITFLIC_RUNNER_WSL`, `AGENTMARSHAL_GITFLIC_RUNNER_CONTAINER`,
`AGENTMARSHAL_WSL_EXE`.

Runner service log показывает lifecycle/executor ошибки и корреляцию по UUID,
но обычно не содержит stdout job script. Если причина там не видна,
воспроизводится job в том же image и с тем же checkout:

```bash
git archive <sha> agentmarshal \
  | /mnt/c/Windows/System32/wsl.exe -d gitflic-runner -- \
      docker run --rm -i alpine:latest sh -c '
        apk add --no-cache bash git jq >/dev/null
        tar -xf -
        bash agentmarshal/tests/negative.sh
      '
```

Команда должна повторять packages/image/script из `.gitflic-ci.yml`. Так для
pipeline `#189` была найдена причина `jq: command not found`: тесты вызывали
launcher, использующий `jq`, а CI job устанавливала только `bash git`.

## Evidence и журнал

- Актуальный transport-контракт живёт в этом документе и скриптах.
- Наблюдение конкретного pipeline можно сохранить append-only событием в
  `.agents/events/<year>/<task>/`, указав pipeline ID, exact SHA, jobs и вывод
  диагностических команд без секретов.
- Исторические handoff/review не переписываются при появлении новых знаний.
  Новая запись ссылается на старую и явно заменяет устаревшее утверждение.
- Pipeline attestation всегда привязана к полному `commitId`; статус другой
  ревизии не считается evidence.

## Следующая автоматизация

Dispatcher может использовать `gitflic-ci.sh` как transport adapter:

1. дождаться terminal status;
2. проверить exact `commitId`;
3. записать событие evidence;
4. запускать reviewer только после `SUCCESS`;
5. передавать Lead/recorder структурированный результат без API token.

Автоматическая проверка pipeline внутри `merge-policy.sh` остаётся отдельным
изменением: сейчас policy требует явный `AGENTMARSHAL_PIPELINE_OK_SHA`, хотя
read-only API уже доступен.
