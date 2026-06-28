# Операции AgentMarshal

Document-ID: agentmarshal-operations
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

Операционный цикл AgentMarshal построен вокруг Git, task contracts, CI,
read-only review и tracked evidence. Дорогая модель не должна висеть в polling
loop: длительные ожидания выполняет координатор или внешний runner.

<!-- Section-ID: lead-cycle -->
## Lead Cycle

1. Создать или выбрать task contract.
2. Проверить runtime config и journal.
3. Подготовить branch/worktree или task-local AgMake runbook.
4. Дождаться exact implementation SHA.
5. Проверить pipeline для этого SHA.
6. Запустить независимое review.
7. Выполнить merge через policy gate.
8. Создать completion branch и закрыть task post-merge.

Базовые проверки:

```bash
agentmarshal/scripts/agentmarshal-config.sh show
agentmarshal/scripts/validate.sh
```

<!-- Section-ID: runner -->
## Runner

До появления автоматического runner координатор выполняет внешний runner
contract вручную. Для cutoff используется AgMake:

```bash
agentmarshal/bin/agmake init --task CR-123 --branch docs/CR-123-example
agentmarshal/bin/agmake lint .agents/tmp/runner/CR-123-runbook.sh
bash .agents/tmp/runner/CR-123-runbook.sh
```

Runbook печатает protocol sections, сохраняет state/logs и при сбое выдаёт
handoff block для модели.

<!-- Section-ID: review -->
## Review

Review запускается только для exact SHA:

```bash
agentmarshal/scripts/review-readonly.sh \
  --task CR-123 \
  --sha <full-sha> \
  --base origin/master \
  --vendor claude
```

Approved review должен содержать `Reviewed-Commit`, `Verdict: approved` и
stable `Finding-IDs`, если есть неблокирующие findings.

<!-- Section-ID: completion -->
## Completion

Task закрывается после фактического merge implementation branch в target.
Completion branch создаётся от актуального target и содержит только journal
transaction:

```bash
agentmarshal/scripts/task-lifecycle.sh complete \
  --task CR-123 \
  --review-task CR-123 \
  --review-file .agents/runs/<review>.md \
  --reviewed-commit <full-sha> \
  --target-ref origin/master
```

Completion MR тоже проходит pipeline, review и merge-policy.

<!-- Section-ID: stats -->
## Stats

Нормализованная статистика хранится в configured `stats_store` (**tracked** Git)
и используется для рейтинга моделей/ролей. Raw runs остаются в `stats_raw_store`
(**ignored**, не отслеживаются Git). Tracked stats не должны содержать секреты,
приватные prompts или полные session transcripts.

Запись normalized stat вручную:

```bash
agentmarshal/scripts/record-agent-stat.sh \
  --project-root /path/to/host \
  --task CR-123 --role <role> --vendor <vendor> --model <model> \
  --profile <profile> --activity <activity> --outcome <outcome> \
  --source-artifact manual
```

Сводки:

```bash
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host summary
agentmarshal/scripts/agentmarshal-stats.sh --project-root /path/to/host ranking
```

`--project-root` опционален при запуске из корня проекта.
