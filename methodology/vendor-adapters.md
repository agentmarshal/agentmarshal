# Vendor-agnostic роли и адаптеры

Требование: **из коробки подключать агентов разных производителей** (сейчас
Claude и Codex; Gemini/Antigravity — под задачи, где объективно сильнее; плюс
агенты «на тестирование»). Поэтому роль определяется **что трогает и как себя
ведёт**, а не каким вендором исполняется.

## Слои

```
agents/<role>.yaml        ← ИСТОЧНИК ИСТИНЫ (vendor-agnostic)
profiles/<profile>.yaml   ← режим запуска: tools/write/network/session
        │  render.sh <role> <vendor>
        ▼
adapters/<vendor>/adapter.sh → нативный конфиг:
   claude  → .claude/agents/<role>.md   (frontmatter + system prompt)
   codex   → .codex/…                   (profile/approvals/subagent) — стаб
   gemini  → … (Antigravity browser/workspace) — стаб
```

Один спек → любой вендор. Сменить исполнителя роли = перегенерировать адаптер,
границы/ветки/identity не меняются (см. personas.md «Model-agnostic»).

Execution profile накладывается поверх роли при запуске. Он может только
сужать доступ роли; task override vendor/model не расширяет capabilities.

## Что несёт спека (для адаптера)

- `scope_allow/scope_deny` → writable roots / permission profile + scope-guard.
- `tools` (vendor-нейтральные) → нативные инструменты (Claude: Bash/Read/Edit…;
  Codex: sandbox commands; Gemini: browser).
- `vendor.preferred/model` → выбор исполнителя (по доступности).
- `vendor.reviewer_must_differ` → ревьюер другого вендора/модели.
- `trial.*` → урезанный профиль для непроверенного агента.
- `human_gate` → approval-правила (Codex `require_escalated` и т.п.).

## Раскладка по вендорам (старт, уточняется benchmark'ом)

| Роль | Preferred | Reviewer |
|---|---|---|
| Lead / Architect | Codex (Lead/merge-gate силён) | Claude Opus |
| Frontend | Claude Sonnet | Codex |
| Backend | Codex | Claude |
| QA / Visual | Codex + Gemini/Antigravity (browser) | Lead |
| Release/Ops | Codex (strict approvals) | Lead |

Это **данные в спеке**, не хардкод — меняются по статистике trial
([trial-agents.md](trial-agents.md)), а не по ощущению.

## Что НЕ менять при смене модели
scope роли · branch prefix · `user.email`/`user.name` worktree · workflow-правила.
Что менять: шаблон коммита, способ загрузки промпта (зависит от агента).
