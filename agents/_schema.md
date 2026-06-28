# Схема role-спеки (`agents/<role>.yaml`)

Спека — **vendor-agnostic источник истины** роли. Per-vendor адаптеры
(`agentmarshal/adapters/*`) рендерят её в нативный конфиг; `scope-guard.sh` и
`persona-status.sh` читают её напрямую. Формат намеренно простой (парсится без
`yq`): скаляры `key: value`, списки `key:` + строки `  - item`.

Роль не является execution profile: фактический режим запуска и tools описаны
в [`../profiles/_schema.md`](../profiles/_schema.md). Профиль может сужать
возможности роли, но не расширять её scope.

| Поле | Тип | Назначение |
|---|---|---|
| `role` | scalar | id роли (= имя файла) |
| `display_name` | scalar | человекочитаемое имя |
| `active` | bool | `false` = зарезервирована (спека есть, агент не онбордён) |
| `branch_prefix` | scalar | префикс веток роли; по нему scope-guard находит спеку |
| `scope_allow` | list | пути-префиксы, которые роль вправе менять. **Пусто (`[]`) = без ограничений** (Lead) |
| `scope_deny` | list | явные запреты (приоритетнее allow) |
| `tools` | list | vendor-нейтральные инструменты; адаптер маппит в native |
| `prompt` | scalar | путь к промпту роли (относительно `agents/`) |
| `vendor.preferred` | scalar | предпочтительный исполнитель (claude/codex/gemini) |
| `vendor.model` | scalar | подсказка модели (не жёстко) |
| `vendor.reviewer_must_differ` | bool | ревьюер ≠ writer (другой vendor/модель) |
| `trial.enabled` | bool | кандидата пробуют изолированно перед закреплением |
| `trial.restrictions` | list | доп.ограничения сверх scope (no-merge, read-only-secrets…) |
| `trial.benchmark` | scalar | как оцениваем (→ methodology/trial-agents.md) |
| `human_gate` | list | действия, которые роль НЕ делает без approval человека |

## Enforced vs advisory (ревью F-009)

Чтобы оператор не принимал метаданные за контроль:

| Поле | Статус | Чем держится |
|---|---|---|
| `scope_allow` / `scope_deny` | **enforced** | `scope-guard.sh` (pre-push + CI), fail-closed |
| `branch_prefix`, `role`, `prompt`, уникальность | **enforced** | `validate.sh` (CI `agentmarshal_validate`) |
| `active` (bool), `vendor.preferred` присутствует | **enforced** | `validate.sh` |
| `vendor.reviewer_must_differ` | **частично** | `merge-policy.sh` (reviewer≠writer, локально) |
| `trial.restrictions` | advisory | пока не исполняется автоматикой |
| `human_gate` | advisory | договорённость + промпт; не машинный гейт |
| `vendor.model` | advisory | подсказка |

Перевод advisory→enforced — отдельной фазой (валидатор политики + диспетчер).

Шаблон новой роли: `agents/_template.yaml`. Границы берутся из
`docs/handbook/07-team/personas.md` («Сводная таблица доступов»).

**Изменил спеку → перегенерируй адаптеры:** `adapters/render.sh <role> <vendor>`.
`.claude/agents/<role>.md` — сгенерированный артефакт, вручную не правят.
