# Схема execution profile (`profiles/<profile>.yaml`)

Execution profile описывает **как запускается агент**, а role-спека
`agents/<role>.yaml` — **за что он отвечает и какие пути ему принадлежат**.
Это разные сущности:

- роль задаёт identity, branch prefix, scope и human gates;
- профиль задаёт режим, инструменты, запись результата и vendor/model defaults;
- task может выбрать профиль и переопределить рекомендуемые vendor/model.

Формат намеренно простой: скаляры верхнего уровня, списки и блок `vendor`.

| Поле | Назначение |
|---|---|
| `profile` | id профиля, совпадает с именем файла |
| `display_name` | человекочитаемое имя |
| `role` | роль, от имени которой выполняется профиль |
| `active` | разрешён ли автоматический запуск |
| `mode` | `review`, `implementation`, `analysis` или `operations` |
| `write_policy` | `none`, `role_scope` или `workspace` |
| `network_policy` | `none`, `read_only` или `allowed` |
| `session_persistence` | сохраняет ли vendor native session |
| `tools` | vendor-neutral capabilities |
| `prompt` | путь относительно `profiles/` |
| `output_recorder` | кто сохраняет результат: `launcher`, `dispatcher`, `agent` |
| `output_directory` | каталог сырых результатов |
| `vendor.preferred` | рекомендуемая исполняющая оболочка |
| `vendor.model` | модель по умолчанию; task может переопределить |

## Инвариант read-only review

Профиль с `write_policy: none` не получает capability `edit`, `write`,
`shell` или `git-write`. Запрет должен держаться launcher/adapter, а не только
текстом prompt. Reviewer возвращает аттестацию, а canonical review сохраняет
доверенный recorder/dispatcher.

## Выбор из task

Task может содержать:

```text
Execution-Profile: qa-readonly
Preferred-Vendor: claude
Preferred-Model: claude-opus-4-8
Model-Policy: preferred
```

`Model-Policy: preferred` разрешает fallback к defaults профиля/роли;
`required` требует указанную модель и оставляет задачу неисполненной, если она
недоступна. Роль при этом не меняется.
