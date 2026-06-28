# Коммуникация и трассируемость: журнал `.agents/`

Агенты не «переписываются в воздухе». Общение — через **артефакты в git**,
чтобы историю можно было не только прочитать, но и расследовать:
**task → handoff → review → ADR → commit/MR**. Если решения нет в `.agents/`,
`docs/`, MR или commit message — формально его не было.

Журнал — [`.agents/`](../../.agents/) (остаётся в проекте при экстракции agentmarshal).

## 4 типа коммуникации

- **Task log** (`.agents/tasks/`) — контракт и состояние задачи.
- **Event** (`.agents/events/2026/<task>/`) — append-only прогресс/handoff/ack
  (минимизирует конфликты на одном task-файле; ADR-0003).
- **Host ADR** (`.agents/decisions/`) — решения конкретного проекта.
- **Framework ADR** (`agentmarshal/docs/adr/`) — архитектура AgentMarshal.
- **Review report** (`.agents/reviews/`) — найденные риски + проверка.
- **Learning note** (`docs/learning/`) — postmortem после инцидента.

Лучше, чем один большой чат-лог: меньше шума, проще аудит.

## Кто чем владеет (журнальные права = scope_allow роли,
[ADR-0003](../docs/adr/ADR-0003-agent-communication-protocol.md))

| Каталог | Владелец (пишет) |
|---|---|
| `tasks/` (контракт, lifecycle open→done) | **Lead** |
| `decisions/` (ADR accept) | **Lead** |
| `reviews/` | **QA / reviewer** (≠ writer) |
| `handoffs/`, `events/` | impl-роль (fe/be), QA |
| фреймворк `agentmarshal/` (спеки, промпты) | **Lead** |

scope-guard механически держит это: impl-роль не правит свой промпт, чужой
task-файл, ADR или ревью. Прогресс пишется в `events/` (append-only), Lead
сводит в task-индекс.

## Шаблоны

### Task (`tasks/open/CR-<id>.md`)
```md
# CR-123: <заголовок>
Owner: <role>          # из [lead frontend backend qa release]
Type: feature|bug|refactor|documentation|technical_debt|security|operations|process
Priority: P0|P1|P2|P3
Branch: <prefix>/<name>
Branch-Type: role|integration
Execution-Profile: <profile-id>        # optional; profiles/*.yaml
Preferred-Vendor: claude|codex|gemini  # optional scheduling hint
Preferred-Model: <model-id>             # optional scheduling hint
Model-Policy: preferred|required        # optional
Status: open           # из [open in_progress in_review blocked done abandoned]
Created: YYYY-MM-DD
Scope:
- <path>
## Context / Plan / Decisions / Verification / Open Questions
```
Заголовок строго `# CR-<id>: <title>`. Завершённую задачу переносят `open/` →
`done/YYYY/` (НЕ удаляют) только командой `task-lifecycle.sh complete` после
merge. Команда выполняется на `completion/*`, созданной от обновлённого target;
изменения доставляются отдельным journal-only MR. До этого task остаётся
`Status: in_review`.

Закрытая задача дополнительно содержит:

```text
Completion-Review: CR-NNN
Reviewed-Commit: <full-sha>
Target-Branch: master
Merged-Commit: <full-sha>
Completed-At: <UTC timestamp>
Completion-Review-Artifact: .agents/reviews/YYYY/<file>.md
Completion-Review-SHA256: sha256:<digest>
```

Поля и Git ancestry проверяет `validate.sh` через `task-lifecycle.sh audit`.

`Owner` определяет роль и scope. `Execution-Profile` определяет фактические
tools/write/network ограничения. Vendor/model в task рекомендуются dispatcher,
но не могут расширить профиль. Подробнее:
[`execution-profiles.md`](execution-profiles.md).

Review-derived follow-up дополнительно получает `Source-Task`,
`Source-Commit`, `Source-Review`, `Source-Findings`, `Due-Before` и
`Triage-Key`. Политика и recorder:
[`review-triage.md`](review-triage.md).

### Handoff (`handoffs/YYYY/CR-<id>-<from>-to-<to>.md`) — обязательный envelope
```md
id: CR-123-HO-001        # уникален среди handoff/event
task: CR-123             # ссылается на существующую задачу
type: handoff
from: <role>
to: <role>
created_at: 2026-06-21T04:42:00Z
branch: fe/CR-123-cars
commit: <full-sha>       # формат SHA
requires_ack: true
status: open             # из [open ack acked closed done]

# Changed / Known risks / Commands run / Please verify
```

### Event (`events/YYYY/CR-<id>/<ts>-<role>-NN.md`) — append-only
```md
id: CR-123-EV-001
task: CR-123
type: progress|note|ack
created_at: 2026-06-21T05:00:00Z
status: open
```

### Review (`reviews/YYYY/CR-<id>-<reviewer>.md`) — структурная identity (R-003)
```md
Task: CR-123
Reviewer-Role: qa            # роль ревьюера
Reviewer-Vendor: codex
Reviewer-Model: gpt-5.5
Reviewer-Email: qa-agent@example.local
Reviewed-Commit: <full-sha>  # ИМЕННО проверенный SHA; смена ветки → review stale
Verdict: approved            # из [approved changes_required blocked rejected]
Finding-IDs: F1, F2          # none, если findings отсутствуют

# Finding / Evidence <file>:<line> / Risk / Suggested fix
# В конце approved review: ```json follow-up-manifest
```
Reviewer-Role/Email сравниваются `merge-policy.sh` со ВСЕМИ авторами и
Co-Authored-By имплементационных коммитов — ревьюер не может быть писателем.
Коммиты, содержащие только evidence-plane артефакты в `reviews/`, `events/`
или `handoffs/`, не считаются implementation; изменение task/policy/code
остаётся implementation независимо от commit message.
Не «кажется нормально», а finding + файл:строка + risk + fix.
Каждый неблокирующий finding из approved review материализуется recorder'ом в
task либо получает явный `accepted_risk`/`wont_fix` в triage event.

### ADR (`decisions/ADR-NNNN-<slug>.md`)
Status / Date / Decision owner / Context / Options / Decision / Consequences.
ADR — только для значимого (архитектура, права, CI, изоляция, tenant). Не на
каждую кнопку. Framework ADR используют Markdown links внутри
`agentmarshal/docs/adr/`; host ADR — ссылки внутри `.agents/decisions/`.

## Правила гейтов

- **Нет task ID — нет merge.** MR ссылается на task + ADR (если был) +
  handoff/review + список команд проверки + (для UI) скриншоты/Playwright +
  файлы вне scope (если есть).
- **Нет merge — нет `done`.** До появления reviewed SHA в target history
  задача остаётся `in_review`, даже если implementation, review и pipeline
  завершены.
- Утверждение «готово» подкреплено **воспроизводимыми проверками** (scope-guard,
  build/tsc, pytest, migration check, Playwright, npm audit, secret scan), а не
  словами агента.
- Reviewer ≠ writer (другой vendor/модель — `vendor.reviewer_must_differ`).

## Сырьё сессий

Полные транскрипты — `scripts/{claude_session_to_md,codex_jsonl_to_md}.py`
(JSONL → md, флаг `--clean`) в `.agents/runs/` (git-ignored). Ключевые решения
вытаскиваются оттуда в task/ADR/review. Вызов экспорта можно повесить на гейт
закрытия сессии.
