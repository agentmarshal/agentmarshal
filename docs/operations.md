# Эксплуатация AgentMarshal

## Ежедневный цикл Lead

### 0. Проверить runtime config

```bash
agentmarshal/scripts/agentmarshal-config.sh show
agentmarshal/scripts/validate.sh --config
```

Конфиг вручную редактируется в `.agents/config/agentmarshal.conf`.

### 1. Создать task contract

```text
Owner
Type / Priority
Status
Scope
Acceptance Criteria
Execution-Profile
Preferred Vendor/Model
Due-Before, если есть
```

Проверка:

```bash
agentmarshal/scripts/validate.sh --journal
```

### 2. Подготовить worktree роли

```bash
agentmarshal/config/worktree/new-agent-worktree.sh <role> <slug>
agentmarshal/scripts/worktree-lifecycle.sh worktree-preflight \
  --worktree <worktree>
agentmarshal/scripts/persona-status.sh <worktree>
```

Перед запуском должны совпадать:

- branch prefix;
- worktree-local Git identity;
- clean tree;
- role spec;
- environment prerequisites.

Путь вычисляется из `worktree_root` и `worktree_pattern`. Все worktrees одного
host находятся под единым root вне основного repository.

`worktree-preflight` обязан пройти до model invocation. Отказ записи в `.git`
останавливает workflow; standalone clone или копирование файлов не являются
fallback.

### 3. Получить handoff

Worker передаёт:

- task;
- branch;
- exact SHA;
- changed behavior;
- commands/evidence;
- known risks;
- requested review focus.

### 4. Проверить CI

```bash
agentmarshal/scripts/gitflic-ci.sh sha <full-sha>
agentmarshal/scripts/gitflic-ci.sh wait <pipeline-id> 1800 15
agentmarshal/scripts/gitflic-ci.sh diagnose <pipeline-id>
```

Approval разрешён только после terminal policy для exact SHA.

CR-029 не требует встроенного dispatcher. Long-running waits выполняются через
external runner contract: до появления автоматического runner координатор
запускает команды вручную, ждёт terminal state вне модели и пишет durable event
с exact SHA/result/artifacts. Модель не должна использоваться как polling loop.

### 5. Запустить независимый review

```bash
agentmarshal/scripts/review-readonly.sh \
  --task CR-NNN \
  --sha <full-sha> \
  --base origin/<default-branch>
```

Raw output хранится в `.agents/runs/` и не является canonical record.

Review, который может занимать минуты, также должен идти через external runner
contract. До автоматизации координатор запускает review вне live model session и
сохраняет raw output/event. Synchronous review допустим только для коротких
локальных проверок или явного operator request.

### 6. Выполнить triage

```bash
agentmarshal/scripts/record-review-followups.sh \
  --review .agents/runs/<review>.md \
  --dry-run

agentmarshal/scripts/record-review-followups.sh \
  --review .agents/runs/<review>.md
```

Blocking findings исправляются до merge и требуют нового review. Approved
non-blocking findings становятся задачами или explicit risk decisions.

### 7. Merge gate

```bash
AGENTMARSHAL_PIPELINE_OK_SHA=<full-sha> \
  agentmarshal/scripts/merge-policy.sh \
    --mr <id> \
    --task CR-NNN \
    --review-file .agents/runs/<review>.md
```

Emergency override требует отдельного incident/event и последующего review.

### 8. Post-merge task completion

После фактического merge обновить refs и создать journal-only ветку от
актуального target. Protected branch напрямую не изменяется:

```bash
git fetch origin --prune
git switch -c completion/CR-NNN origin/master

agentmarshal/scripts/task-lifecycle.sh complete \
  --task CR-NNN \
  --review-task CR-NNN \
  --review-file .agents/runs/<review>.md \
  --reviewed-commit <full-sha> \
  --target-ref origin/master

git add .agents/
git commit -m "chore(agentmarshal): complete CR-NNN"
git push -u origin completion/CR-NNN
```

Для integration batch можно передать несколько `--task`; все они получат одну
`Completion-Review`. Команда требует clean `completion/*` branch на exact
target SHA, проверяет ancestry, канонизирует review и переносит задачи в
`done`.

Completion branch проходит pipeline и независимый review своего exact head.
`merge-policy.sh` разрешает для неё `Status: done`, но только если diff
ограничен `.agents/{tasks,reviews,events,handoffs}/` и completion audit
проходит. После этого branch сливается в protected target обычным MR.
`validate.sh` вызывает `task-lifecycle.sh audit`.

В GitFlic single-branch checkout target ref может отсутствовать. CI передаёт
`AGENTMARSHAL_AUDIT_COMPLETION_HEAD="$CI_COMMIT_SHA"` и
`AGENTMARSHAL_AUDIT_TARGET_BRANCH=master` валидатору. Fallback принимается только
для exact `completion/*` HEAD и matching `Target-Branch`; он полагается на
соседний blocking `scope_guard`, который независимо проверяет branch
относительно trusted `master`. Локальный audit без target ref и без этой явной
аттестации падает fail-closed.

### 9. Worktree finalization и cleanup

После интеграции и push:

```bash
agentmarshal/scripts/worktree-lifecycle.sh finalize \
  --integration-sha <full-sha> \
  --integration-ref <branch> \
  --require-pushed

agentmarshal/scripts/worktree-lifecycle.sh cleanup-ready \
  --worktree <worker-worktree> \
  --integration-sha <full-sha> \
  --integration-ref <branch> \
  --require-pushed
```

Временный worktree удаляется только после успешного worktree finalization.
Task lifecycle закрывается отдельно, после merge в target branch. Наличие тех
же файлов в primary без commit/ref не является finalization.

## Worker workflow

```text
read task → persona-status → implement in role scope → tests
→ scope-guard → commit/push → handoff exact SHA
```

Worker не:

- меняет own role/profile policy;
- принимает ADR;
- записывает canonical approval своей работы;
- мержит без Lead policy;
- использует generic branch для обхода provenance.

## QA workflow

QA:

- проверяет чужой exact SHA;
- отделяет blocking от non-blocking;
- пишет findings с stable IDs;
- возвращает отчёт на `review_language` из host config;
- для approved добавляет `Finding-IDs` и complete follow-up manifest;
- не материализует tasks при read-only profile.

## Recorder workflow

Recorder является trusted write-side процесса:

- валидирует verdict/SHA/source task;
- валидирует manifest schema;
- проверяет полное и однократное покрытие findings;
- назначает следующий task ID;
- пишет `Source-*`, `Due-Before`, `Triage-Key`;
- создаёт append-only event;
- повторный запуск не создаёт дублей.

## Debt scheduling

Dispatcher поднимает задачу, если:

- наступил `Due-Before`;
- активируется capability, перед которой долг обязателен;
- задача `P1`;
- накопилась группа однотипных `P2`;
- наступила плановая debt-сессия.

Security debt не смешивается с обычным refactoring, если у него другая граница
риска или milestone.

## Статистика

Review launcher автоматически пишет ignored raw metric:

```text
.agents/runs/stats/RUN-*.json
```

Trusted recorder материализует запись:

```bash
agentmarshal/scripts/record-agent-stat.sh \
  --input .agents/runs/stats/<run>.json
```

Для implementation/operations dispatcher может передать метрики CLI:

```bash
agentmarshal/scripts/record-agent-stat.sh \
  --task CR-123 --role frontend --vendor codex --model <model> \
  --profile frontend-default --activity implementation --outcome success \
  --commit <sha> --duration-seconds 900 --tests-passed 3 \
  --human-interventions 1 --source-artifact .agents/events/...md
```

Сводка:

```bash
agentmarshal/scripts/agentmarshal-stats.sh summary
agentmarshal/scripts/agentmarshal-stats.sh summary --trial true --json
agentmarshal/scripts/agentmarshal-stats.sh ranking
```

Перед ручной нормализацией implementation можно запускать единым launcher:

```bash
agentmarshal/scripts/run-agent-task.sh \
  --task CR-123 --vendor codex --model <model>
```

После cross-review и adjudication trusted recorder создаёт отдельную оценку:

```bash
agentmarshal/scripts/record-agent-evaluation.sh --input assessment.json
```

Run facts не редактируются при изменении scoring formula.

## Диагностика

### Validator падает

Запускать по частям:

```bash
agentmarshal/scripts/validate.sh --specs
agentmarshal/scripts/validate.sh --profiles
agentmarshal/scripts/validate.sh --config
agentmarshal/scripts/validate.sh --journal
```

### Scope guard падает

Проверить:

- base/head resolvable;
- branch prefix;
- author email role;
- changed paths;
- trusted default-branch SHA;
- API manifest shape.

### Pipeline упал

```bash
agentmarshal/scripts/gitflic-ci.sh diagnose <pipeline>
agentmarshal/scripts/gitflic-ci.sh job <job>
agentmarshal/scripts/gitflic-ci.sh runner-log <job>
```

Если stdout API недоступен, воспроизвести exact image/packages/script.

### Recorder отказался

Проверить:

- `Verdict: approved`;
- полный `Reviewed-Commit`;
- source task существует;
- `Finding-IDs` совпадает с manifest;
- каждый finding покрыт ровно один раз;
- нет stale lock/process;
- `.agents/tmp` доступен recorder.

### После agent run файлы есть, но primary HEAD старый

Не делать новый commit поверх уже существующей истории. Проверить clone/bundle,
импортировать refs через `git fetch`, побайтно сверить tree и передвинуть
primary branch штатным Git-механизмом. После восстановления обязательно
запустить `worktree-lifecycle.sh finalize`.

## Регрессионные проверки

```bash
bash agentmarshal/scripts/validate.sh
bash agentmarshal/tests/negative.sh
bash -n agentmarshal/scripts/*.sh
git diff --check
```

Перед release AgentMarshal те же проверки запускаются в минимальном supported
runtime image.
