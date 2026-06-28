# Triage неблокирующих findings

Неблокирующее замечание не должно оставаться только внутри review или чата.
После `Verdict: approved` каждый finding получает явную disposition и попадает
в отслеживаемый AgentMarshal backlog либо в журнал принятого решения.

## Disposition

| Disposition | Когда применяется | Результат |
|---|---|---|
| `blocking` | риск не позволяет принять текущий SHA | `changes_required`; исправление в текущей задаче и новый review |
| `follow_up` | текущий SHA допустим, но долг нужно устранить | новая задача в `.agents/tasks/open/` |
| `accepted_risk` | риск осознанно принимается Lead | append-only triage event с обоснованием |
| `wont_fix` | исправление нецелесообразно | append-only triage event с обоснованием |
| `post_cutoff` | finding принимается как отложенный после cut-off | append-only triage event с обоснованием |
| `existing_task` | finding уже покрыт существующей задачей | ссылка на target task + append-only triage event |
| `debt_bundle` | finding входит в уже сформированный пакет технического долга | ссылка на target task + append-only triage event |
| `duplicate` | finding дублирует уже зарегистрированный backlog item | ссылка на target task + append-only triage event |

`P0` не бывает неблокирующим. `P0`, а обычно и `P1`, требует
`changes_required`. Исключение для `P1` должно иметь короткий `Due-Before`.
В `cutoff_freeze` recorder не создаёт новые active `P3`, а `P2` допускает
только если `Due-Before` совпадает с `active_milestone`. Остальные случаи
нужно оформлять как `existing_task`, `debt_bundle`, `duplicate` или
`post_cutoff`.

## Поля задач

Все задачи содержат:

```text
Type: feature|bug|refactor|documentation|technical_debt|security|operations|process
Priority: P0|P1|P2|P3
```

Задачи, созданные из review, дополнительно содержат:

```text
Source-Task: CR-001
Source-Commit: <full-sha>
Source-Review: CR-001@<full-sha>
Source-Findings: F1, F2
Due-Before: CR-029
Triage-Key: sha256:<hash>
```

`Due-Before` принимает `none`, ISO-date, `CR-NNN` или milestone slug.
Для `existing_task`, `debt_bundle` и `duplicate` `target` обязателен; для
`post_cutoff` target не нужен.
`Triage-Key` делает recorder идемпотентным: повторная обработка того же набора
findings не создаёт дубль.

## Машинный manifest review

Approved review всегда завершает отчёт fenced JSON-блоком:

````markdown
```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1", "F2", "F3"],
  "tasks": [
    {
      "title": "Усилить тесты GitFlic CI transport",
      "type": "technical_debt",
      "priority": "P2",
      "owner": "lead",
      "source_findings": ["F1", "F2"],
      "due_before": "CR-029",
      "risk": "Необработанные transport-сценарии могут сорвать manual runner mock или будущий external runner.",
      "acceptance_criteria": [
        "Добавлены тесты HTTP 500 и timeout.",
        "Документация соответствует exit codes."
      ],
      "scope": [
        "agentmarshal/scripts/gitflic-ci.sh",
        "agentmarshal/tests/"
      ]
    }
  ],
  "non_task": [
    {
      "source_findings": ["F3"],
      "disposition": "accepted_risk",
      "rationale": "Риск ограничен локальной однопользовательской средой."
    }
  ]
}
```
````

Схема: `agentmarshal/schemas/review-follow-up-manifest.schema.json`.

Инварианты recorder:

- review имеет `Verdict: approved`, полный `Reviewed-Commit` и source task;
- `Finding-IDs` точно совпадает с `review_findings` встроенного manifest;
- каждый ID из `review_findings` встречается ровно один раз в `tasks` или
  `non_task`;
- неизвестный тип, priority, owner, disposition или malformed JSON блокируют
  запись;
- reviewer предлагает только `follow_up`; `accepted_risk` и `wont_fix`
  подтверждает доверенный Lead/recorder;
- recorder пишет append-only triage event с хэшами review и manifest.

## Recorder

```bash
agentmarshal/scripts/record-review-followups.sh \
  --review .agents/runs/CR-001-qa-review-<sha>-<time>.md
```

Для legacy review без встроенного блока:

```bash
agentmarshal/scripts/record-review-followups.sh \
  --review <approved-review.md> \
  --source-task CR-001 \
  --manifest .agents/tmp/CR-001-followups.json
```

Сначала полезно запустить `--dry-run`. Команда изменяет только record-plane:
`.agents/tasks/open/` и `.agents/events/`.

## Планирование debt-сессий

Dispatcher выбирает backlog в таком порядке:

1. `Due-Before` наступил или связан с активируемой возможностью.
2. `Priority: P1`.
3. Накопилось не менее пяти задач `P2` одного scope.
4. Плановая debt-сессия занимает примерно 15–20% агентного времени.

Закрытие follow-up требует проверки исходного риска и ссылки на
`Source-Findings`; простого изменения статуса недостаточно.
