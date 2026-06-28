# Codex adapter (стаб — рендер в Фазе 2)

Цель: `agents/<role>.yaml` → нативный конфиг Codex (`.codex/`).

Целевой формат (по сессии Codex, `.agents/runs/codex_session_20260605_clean.md (локально, git-ignored)`):
- Codex силён как **Lead / reviewer / merge-gate / backend** — приоритетные роли
  для этого адаптера.
- У Codex есть worktrees, review pane, **sandbox/approvals**, profiles,
  subagents — маппим сюда:
  - `scope_allow`/`scope_deny` → permission profile (writable roots) + наш
    `scope-guard.sh` как pre-push/CI (Codex profile в его сессии уже даёт read
    на `.agents`, write на workspace root).
  - `human_gate` → approval rules (require_escalated для prod/destructive).
  - `prompt` → системный промпт профиля.
  - `trial.restrictions` → урезанный profile (no-merge, read-only secrets).

Когда реализуем `adapter.sh`: определить функцию `render_codex <role>`,
использующую `spec_scalar` / `spec_list` / `spec_nested` из `render.sh`
(см. `adapters/claude/adapter.sh` как референс).

Сейчас Codex-роли (lead/backend) онбордятся вручную по спеке; scope-guard и
.agents-журнал уже vendor-нейтральны и работают для Codex как есть.
