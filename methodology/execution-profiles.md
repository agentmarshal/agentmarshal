# Execution profiles: воспроизводимый режим запуска агента

Роль и execution profile нельзя смешивать.

| Сущность | Отвечает на вопрос | Источник истины |
|---|---|---|
| Role | Кто отвечает за работу и какие пути ему принадлежат? | `agents/<role>.yaml` |
| Execution profile | С какими инструментами и ограничениями запускается сессия? | `profiles/<profile>.yaml` |
| Task scheduling | Какой vendor/model рекомендуется для конкретной задачи? | `.agents/tasks/...` |

Одна роль может иметь несколько профилей. Например, QA:

- `qa-readonly` — независимый reviewer без записи и shell;
- будущий `qa-test-author` — запись только в test scope;
- будущий `qa-visual` — browser/computer tools и артефакты screenshots.

## Почему prompt недостаточно

Фраза «не изменяй файлы» является advisory. Ограничение становится enforced,
только когда adapter/launcher не выдаёт агенту write-capabilities.

Для `qa-readonly` это означает:

- Claude запускается с `--safe-mode`, tools ограничены `Read,Grep,Glob`;
- Codex запускается с `--sandbox read-only`, `--ephemeral`,
  `approval_policy=never` и без user config;
- launcher разворачивает `git archive` reviewed SHA во временный snapshot и
  прикладывает exact unified diff; reviewer не читает mutable worktree;
- отсутствуют `Edit`, `Write`, `Bash`, browser/computer;
- native session не сохраняется;
- результат записывает launcher в ignored `.agents/runs/`;
- canonical `.agents/reviews/` заполняет recorder/dispatcher отдельно.

## Запуск

```bash
agentmarshal/scripts/review-readonly.sh \
  --task CR-001 \
  --sha <full-sha> \
  --vendor claude \
  --model claude-opus-4-8
```

Launcher читает defaults и tools из `profiles/qa-readonly.yaml`. CLI overrides
разрешены для vendor/model, но не могут расширить capabilities профиля.
Поддерживаются Claude и Codex, что позволяет делать взаимное независимое
review.

## Выбор профиля и модели в task

```text
Owner: qa
Execution-Profile: qa-readonly
Preferred-Vendor: claude
Preferred-Model: claude-opus-4-8
Model-Policy: preferred
```

- `Owner` остаётся источником role identity и scope.
- `Execution-Profile` выбирает режим исполнения.
- `Preferred-*` — scheduling hint для dispatcher.
- `Model-Policy: preferred` разрешает fallback.
- `Model-Policy: required` запрещает fallback.

Task override не имеет права расширять tools/write/network policy профиля.

## Локальные vendor-конфиги

`.claude/`, `.codex/` и аналогичные каталоги могут быть git-ignored и
машиноспецифичны. Они не являются источником истины. Воспроизводимые данные
профиля и launcher живут внутри `agentmarshal/`.
