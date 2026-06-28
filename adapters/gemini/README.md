# Gemini / Antigravity adapter (стаб — рендер позже)

Цель: `agents/<role>.yaml` → нативный конфиг Gemini CLI / Google Antigravity.

Целевое назначение (по сессии Codex):
- Лучший кандидат на **Visual QA / Browser agent** (Antigravity: Agent Manager,
  Editor, **Browser** с записью действий, artifacts). Приоритетная роль —
  `qa` (visual verification вместо ручного human-gate).
- Antigravity поддерживает разные reasoning-модели (Gemini, Claude Sonnet/Opus,
  GPT-OSS) — то есть это ещё и **исполняющая оболочка**, не только модель.

Маппинг при реализации `render_gemini <role>`:
- `tools: browser` → включить browser-control; артефакты (screenshots, traces)
  складывать в `.agents/runs/` (ignored) + ключевые в `.agents/reviews/`.
- `scope_allow` → ограниченный workspace (frontend-only / preview env).
- `human_gate` + строгие permissions: НЕ давать prod secrets / SSH / infra,
  browser auto-execute — только request-review.
- `trial.enabled: true` (qa) — Antigravity удобен как первый trial-агент.

Привлекается «на тестирование» и под задачи, где объективно сильнее (visual,
browser-driven E2E). Закрепление роли — по benchmark (methodology/trial-agents.md).
