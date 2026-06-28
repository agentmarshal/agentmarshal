# Trial-агенты: взаимное ревью, измерения и рейтинг

Роли закрепляются за вендором/моделью по воспроизводимым данным. Trial не
пытается одним числом определить «лучшую модель вообще»: сравнение ведётся
отдельно по activity, task class и одинаковой сложности.

## Два типа данных

### Operational observations

Реальные задачи проекта измеряют надёжность, автономность, стоимость и
количество подтверждённых review findings. Они полезны для назначения ролей,
но не дают полного ground truth: неизвестно, сколько дефектов пропустил
reviewer.

### Controlled benchmark

Эквивалентные fixtures запускаются для каждой модели от одного base commit.
Для review benchmark заранее известны или намеренно внесены дефекты. Только
такие прогоны дают полный review score с измеримой recall.

Operational и controlled результаты нельзя объединять в одну выборку.

## Cross-review

Writer и reviewer обязаны различаться по vendor:

| Implementation | Review |
|---|---|
| Codex | Claude |
| Claude | Codex |

Один агент не материализует собственную оценку. Launcher пишет raw evidence,
trusted recorder создаёт normalized run, а Lead/dispatcher подтверждает
findings и создаёт evaluation.

## Trial batch

Перед запуском создаётся `.agents/trials/YYYY/TRIAL-*.json`. Batch фиксирует:

- единый immutable `base_commit`;
- task class и difficulty;
- executor/reviewer vendor и model;
- разрешённый scope;
- `scoring_version`;
- минимальный размер устойчивой выборки.

Параллельные задачи получают разные worktrees и непересекающиеся scope. Если
обе задачи меняют общий policy, journal index или CI-файл, они не являются
независимыми и должны выполняться последовательно.

## Запуск и сбор фактов

Implementation:

```bash
agentmarshal/scripts/run-agent-task.sh \
  --task CR-123 --vendor codex --model <model>
```

Review противоположным вендором:

```bash
agentmarshal/scripts/review-readonly.sh \
  --task CR-123 --sha <full-sha> \
  --vendor claude --model <model>
```

Оба launcher пишут content-free raw records в `.agents/runs/stats/`. После
commit и проверки pipeline dispatcher создаёт tracked run через
`record-agent-stat.sh`. Raw запись не редактируется: commit SHA, число тестов
и итоговый outcome передаются в новую normalized запись.

## Оценка implementation: trial-v1

Максимум 100:

| Компонент | Баллы |
|---|---:|
| Acceptance criteria | 20 |
| Pipeline exact SHA | 20 |
| Качество после подтверждённых findings | 25 |
| Diff discipline | 15 |
| Автономность | 10 |
| Нормализованная эффективность | 10 |

Quality начинается с 25; атрибутируемый implementation blocking finding
вычитает 15, P2 — 7, P3 — 2. Reviewer finding вне task Scope может быть
подтверждённым для precision reviewer-а, но не попадает в
`implementation_findings`. Autonomy начинается с 10; human intervention
вычитает 3, rework cycle — 2. Компоненты не уходят ниже нуля.

Невалидный provenance или scope violation делает implementation score равным
нулю. Это invalid run, а не «немного менее хороший» результат.

`diff_discipline_points` и `efficiency_points` назначаются только после
сравнения с задачами того же batch/class/difficulty. До появления peer-run
оценка остаётся pending.

## Оценка review: trial-v1

Максимум 100:

| Компонент | Баллы |
|---|---:|
| Recall известных дефектов | 30 |
| Precision подтверждённых findings | 25 |
| Severity calibration | 20 |
| Actionability | 15 |
| Нормализованная эффективность | 10 |

Если `known_defects > 0`, review получает `score_status=full`. Для реальной
задачи без известного ground truth recall вычислить нельзя: оставшиеся
компоненты нормализуются в provisional score. Provisional score показывается
отдельно и не может сделать рейтинг устойчивым.

False positive, severity и actionability подтверждает adjudicator. Спорный
finding получает `adjudication_status=disputed`; такая evaluation не входит в
рейтинг до разрешения спора.

## Run facts и evaluation

Неизменяемые факты:

```text
.agents/stats/runs/YYYY/RUN-*.json
```

Пересчитываемая по версионированной формуле оценка:

```text
.agents/stats/evaluations/YYYY/EVAL-*.json
```

Recorder:

```bash
agentmarshal/scripts/record-agent-evaluation.sh --input assessment.json
```

Evaluation обязана ссылаться на существующие executor/reviewer runs, task,
trial batch и evidence. Формула записана в recorder и маркируется
`scoring_version=trial-v1`.

## Рейтинг

```bash
agentmarshal/scripts/agentmarshal-stats.sh ranking
agentmarshal/scripts/agentmarshal-stats.sh ranking --task-class ci --json
```

Рейтинг:

- раздельный для implementation и review;
- раздельный по task class;
- использует median, а не среднее;
- включает только `adjudication_status=confirmed`;
- считается устойчивым при трёх и более сопоставимых evaluations;
- для review требует `score_status=full`.

Первые два cross-review прогона проверяют процесс. Они не являются
достаточной выборкой для назначения постоянного победителя.

## Остановка автоматики

Dispatcher прекращает автоматический цикл при:

- scope/provenance violation;
- blocking finding после исчерпания retry budget;
- споре, который нельзя разрешить тестом или acceptance contract;
- повторяющейся инфраструктурной ошибке;
- необходимости merge, production или secrets gate.
