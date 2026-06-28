# Runtime-конфигурация и статистика

## Назначение

AgentMarshal разделяет framework policy и параметры конкретного host:

- `agentmarshal/` содержит код, схемы, роли и методики;
- `.agentmarshal/project.json` (fresh) или `.agents/config/agentmarshal.conf`
  (adopted) содержит вручную редактируемые runtime-параметры;
- `stats_raw_store` (по умолчанию `.agentmarshal/journal/runs/stats/`) содержит
  сырые метрики запусков — **ignored**, не отслеживается Git;
- `stats_store` (по умолчанию `.agentmarshal/journal/stats/runs/YYYY/`) содержит
  нормализованную статистику без содержимого prompt/response — **tracked**,
  отслеживается Git;
- `evaluation_store` содержит adjudicated оценки, отдельно от неизменяемых
  фактов запуска — также **tracked**.

Runtime-конфиг имеет формат `key=value`. Это data file: скрипты разбирают его
без `source`, поэтому значение не может выполнить shell-команду.

ADR-0007 вводит `.agentmarshal/project.json`, configurable paths и
рекомендуемый journal `.agentmarshal/journal/`. `init --adopt-existing` явно
регистрирует существующий layout (legacy `.agents/`); scripts используют
configured paths из project.json.

## Параметры

| Ключ | Пример | Назначение |
|---|---|---|
| `schema` | `1` | версия формата конфигурации |
| `review_language` | `ru` | BCP 47-подобный language tag для содержательной части review |
| `active_roles` | `lead,frontend,qa` | роли, разрешённые к запуску на этом host |
| `operating_mode` | `cutoff_freeze` | `normal` либо release-focused admission control |
| `active_milestone` | `agentmarshal-v0.1-cutoff` | milestone для допуска P2 в active backlog |
| `backlog_amplification_limit` | `0.3` | максимальное отношение новых active follow-up к completed tasks |
| `worktree_root` | `../agentmarshal-host.worktrees` | абсолютный или относительный к repository root каталог worktrees |
| `worktree_pattern` | `{repo}.{alias}` | имя worktree; поддерживает `{repo}` и обязательный `{alias}` |
| `stats_enabled` | `true` | включает автоматический сбор и trusted recording метрик |
| `stats_store` | `.agentmarshal/journal/stats/runs` | **tracked** normalized records (Git-tracked) |
| `evaluation_store` | `.agentmarshal/journal/stats/evaluations` | **tracked** versioned scores (Git-tracked) |
| `stats_raw_store` | `.agentmarshal/journal/runs/stats` | **ignored** launcher records (not Git-tracked) |
| `stats_retention_days` | `365` | срок хранения raw records для dispatcher/maintenance |

`active_roles` не заменяет role specs. Поле `active: true` в
`agentmarshal/agents/<role>.yaml` означает, что capability доступна framework.
`active_roles` выбирает доступное сейчас подмножество для конкретного проекта.

После ручного изменения:

```bash
agentmarshal/scripts/agentmarshal-config.sh show
agentmarshal/scripts/validate.sh --config
```

Для автоматизации путь можно переопределить:

```bash
AGENTMARSHAL_RUNTIME_CONFIG=/path/to/agentmarshal.conf \
  agentmarshal/scripts/validate.sh --config
```

## Resource routing

Resource policy хранится как host-owned JSON и валидируется fail-closed по
[`../schemas/resource-routing.schema.json`](../schemas/resource-routing.schema.json).
Model ID и reasoning effort задаются раздельно для tiers
`economy|standard|critical`.

Детерминированный route можно проверить без запуска модели:

```bash
agentmarshal/scripts/resolve-resource-route.sh \
  --policy .agentmarshal/config/resource-routing.json \
  --request task-route-request.json
```

Resolver возвращает выбранные vendor/model/effort и следующий escalation tier.
Политика не должна использовать mutable alias вида `latest`; доступность
конкретной модели проверяет vendor launcher preflight.

## Worktrees

Все role worktrees размещаются в одном каталоге вне основного repository.
При repository root `/path/to/agentmarshal-host` текущая конфигурация даёт:

```text
/path/to/agentmarshal-host.worktrees/
  agentmarshal-host.fe
  agentmarshal-host.be
  agentmarshal-host.qa
  agentmarshal-host.ops
```

Фактический root можно узнать без вычислений вручную:

```bash
agentmarshal/scripts/agentmarshal-config.sh path worktree_root
```

Создание или подготовка role worktree:

```bash
agentmarshal/config/worktree/new-agent-worktree.sh frontend <task-slug>
```

Скрипт откажется запускать роль, которой нет в `active_roles`. Каталог
worktree обязан находиться вне project root: это проверяет `validate.sh`.
Worktree даёт инженерную изоляцию Git, но не является security boundary;
границы записи обеспечивает `scope-guard`.

При переносе существующего worktree сначала завершить или сохранить работу,
затем удалить старую регистрацию штатной командой `git worktree remove` и
заново вызвать helper. Перемещать каталог вручную нельзя.

## Два уровня статистики

Implementation/review launcher или dispatcher пишет raw record после каждого запуска. Запись
содержит usage/cost и машинные метрики, но не prompt, ответ модели, секреты или
фрагменты исходного кода. Raw records нужны для диагностики и могут быть
удалены после `stats_retention_days`.

Vendor/API failure также создаёт raw record с `outcome=failed`; такой запуск не
создаёт review и не может считаться approval.

Trusted recorder проверяет record и переносит его в tracked store:

```bash
agentmarshal/scripts/record-agent-stat.sh \
  --project-root /path/to/host \
  --input <stats_raw_store>/2026/<RUN-id>.json
```

Для запуска, у которого нет vendor-метрик, recorder принимает поля напрямую:

```bash
agentmarshal/scripts/record-agent-stat.sh \
  --project-root /path/to/host \
  --task CR-123 \
  --role frontend \
  --vendor codex \
  --model <model> \
  --profile frontend-default \
  --activity implementation \
  --outcome success \
  --commit <full-sha> \
  --duration-seconds 900 \
  --tests-passed 3 \
  --human-interventions 1 \
  --source-artifact manual
```

`--project-root` опционален, когда команда запускается из корня проекта или
из git-submodule checkout. Для fresh-host проектов он рекомендован явно.

Поле `activity` — host-extensible safe string вида `^[a-z][a-z0-9-]*$`;
стандартные значения: `implementation`, `review`, `visual-qa`, `operations`,
`analysis`. Host-specific values (например, `research-deep`) допустимы.

Поле `outcome` принимает значения: `success`, `approved`, `changes_required`,
`blocked`, `rejected`, `failed`, `canceled`, `partial`, `negative`.

Recorder:

- требует существующие task и role;
- валидирует типы, значения и полный SHA;
- создаёт стабильный `RUN-*` ID;
- пишет атомарно;
- идемпотентен для уже записанного идентичного record;
- отказывает при конфликте ID.

Implementation launcher:

```bash
agentmarshal/scripts/run-agent-task.sh \
  --task CR-123 --vendor codex --model <model>
```

Он требует чистый worktree, прикладывает task contract, запрещает commit/push,
проверяет task-specific Scope и пишет raw implementation record. Commit,
pipeline и test results добавляет trusted dispatcher при нормализации.

## Нормализованные метрики

Схема: `agentmarshal/schemas/agent-run-stat.schema.json`.

Обязательные группы:

- provenance: task, role, vendor, model, profile, activity, commit;
- result: outcome, trial;
- effort: duration, turns, human interventions, retries;
- quality: scope violations, tests, findings;
- change size: files, additions, deletions;
- usage: input/output tokens и cost;
- audit link: source artifact.

Нулевое значение означает «не предоставлено или не применимо», если launcher
не умеет отличить эти состояния. Поэтому сравнение моделей должно использовать
одинаковый launcher, benchmark и acceptance criteria.

## Сводки

```bash
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host summary
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host summary --trial true
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host summary --role qa --vendor claude --json
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host list --model <model> --json
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host ranking
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host ranking --task-class ci --json
```

`--project-root` опционален, когда команда запускается из корня проекта.

Статистика является evidence для решения о назначении модели, но не заменяет
review. Маленькая выборка и задачи разной сложности не дают корректного
сравнения.

## Evaluation и рейтинг

Run record хранит измеренный факт и не переписывается после изменения формулы.
Evaluation ссылается на executor/reviewer runs, trial batch и evidence:

```bash
agentmarshal/scripts/record-agent-evaluation.sh --input assessment.json
```

Формула `trial-v1`, operational/controlled режимы, full/provisional review
score и правила устойчивой выборки описаны в
[`../methodology/trial-agents.md`](../methodology/trial-agents.md).

## Retention и приватность

- normalized tracked records не удаляются автоматически;
- `stats_retention_days` относится к ignored raw records;
- очистку raw store выполняет dispatcher или плановая maintenance-задача;
- tracked record не содержит содержательного model output;
- секреты и токены запрещены на обоих уровнях;
- стоимость может быть `0`, если vendor её не сообщил.

Перед merge:

```bash
agentmarshal/scripts/validate.sh --config
agentmarshal/scripts/validate.sh --journal
agentmarshal/scripts/agentmarshal-stats.sh summary --json
```
