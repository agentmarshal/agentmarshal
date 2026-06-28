# agentmarshal CHANGELOG

## v0.1 cutoff qualification — 2026-06-24

- Added `agentmarshal/tests/qualification.sh` as the release qualification gate
  for standalone AgentMarshal extraction.
- Qualification covers full validation, bilingual docs parity, bootstrap,
  provider SPI, resource routing, negative gates, preset init/doctor,
  host-local plugin activation, overprivileged plugin rejection and tracked
  snapshot contaminant scan.
- Resolved/default plugins requesting `permissions.git_write=true` are rejected
  by `agentmarshal doctor` for v0.1 fail-closed least-privilege policy.
- Published sanitized qualification report in
  `agentmarshal/docs/qualification-report.md`.

## Phase 1 CI completion audit remediation — 2026-06-23

- INC-0003 фиксирует падение completion pipeline #202: GitFlic single-branch
  checkout не создавал `origin/master`, требуемый task-lifecycle audit.
- Audit получает явный exact-SHA fallback только для `completion/*` CI head;
  без target ref и аттестации остаётся fail-closed.
- Fallback является частью составного gate с blocking trusted `scope_guard`,
  который проверяет source branch относительно provider default branch.
- Негативные тесты воспроизводят настоящий single-branch clone.

## Phase 1 post-merge task completion — 2026-06-23

- INC-0002 фиксирует преждевременное закрытие CR-001/CR-011 до merge.
- `merge-policy.sh` требует `Status: in_review` и принимает explicit raw
  `--review-file`, не меняющий reviewed source SHA.
- Reviewer independence исключает evidence-only commits (`reviews/events/
  handoffs`) из implementation writers; изменение code/task/policy по-прежнему
  делает автора writer.
- Read-only launcher добавляет trusted plain-text machine header с task,
  reviewer identity, exact SHA, verdict и finding IDs поверх vendor output.
- Merge policy одинаково читает plain и Markdown-bold review metadata.
- Добавлен `task-lifecycle.sh complete|audit`: ancestry target history,
  canonical review, SHA256 и машинно проверяемые completion fields.
- `validate.sh` связывает task status с каталогом и запрещает `done` без merge
  evidence.
- Protected target поддерживается без direct push: completion готовится на
  `completion/*` от обновлённого target и доставляется journal-only MR.
- Scope guard, CI rules и merge-policy распознают `completion/*`;
  merge-policy разрешает `Status: done` только при journal-only diff и
  успешном task-lifecycle audit.
- CR-001 и CR-011 возвращены в `in_review`; финальная интеграция ведётся CR-017.

## Phase 1 worktree lifecycle remediation — 2026-06-23

- INC-0001 фиксирует split-history инцидент: standalone clones содержали семь
  коммитов, а скопированные файлы оставили primary HEAD позади на 45 paths.
- Добавлен `worktree-lifecycle.sh`: Git metadata preflight, registered
  common-dir worktree check, exact integration finalization и cleanup gate.
- Worker launcher и worktree helper теперь fail-closed при read-only `.git`;
  clone/copy fallback запрещён.
- Finalization требует clean primary tree, exact integration SHA и опционально
  exact pushed upstream.

## Phase 1 reciprocal trials and rating — 2026-06-23

- Read-only review launcher поддерживает Claude и Codex с одинаковым
  launcher-owned recorder pattern.
- Reviewer читает immutable archive конкретного SHA и получает exact unified
  diff, поэтому stale/mutable worktree не может подменить review evidence.
- Добавлен implementation launcher для Claude/Codex с task Scope check и
  content-free raw metrics.
- Trial batch фиксирует base SHA, cross-vendor assignments и scoring version.
- Run facts отделены от adjudicated evaluations; `trial-v1` считает
  implementation/review score и маркирует full/provisional review.
- Ranking агрегирует median отдельно по activity/task class и не объявляет
  устойчивость до трёх сопоставимых прогонов.

## Phase 1 cutoff planning — 2026-06-22

- ADR-0007 зафиксировал public `init/doctor`, `.agentmarshal/project.json`,
  configurable host paths и migration legacy `.agents/`.
- GitFlic должен стать provider adapter; до cutoff обязателен mock provider,
  GitHub/GitLab получают capability contract/stubs.
- Public framework docs выпускаются на русском и английском с CI parity checks.
- CR-007..CR-010 формализуют подготовку bootstrap/provider/docs и последний
  standalone snapshot/submodule cutoff.

## Phase 1 runtime config and statistics — 2026-06-22

- Добавлен безопасный host config `.agents/config/agentmarshal.conf`: review
  language, active roles, worktree root/pattern и stats policy.
- Worktree helper использует единый configurable root и блокирует неактивные
  роли; QA явно активирована для `qa-readonly`.
- Review launcher автоматически собирает content-free raw metrics.
- Неуспешные vendor-вызовы также записываются с `outcome=failed`, не выдавая
  ошибку транспорта за review.
- Добавлены normalized stats recorder, schema, tracked store и агрегатор
  `agentmarshal-stats.sh` для trial/model comparison.

## Phase 1 internal architecture docs — 2026-06-22

- Добавлен self-contained `docs/`: architecture, host contract, operations,
  extraction readiness и framework ADR index.
- ADR-0001..0003 перенесены из host `.agents/decisions/` в `docs/adr/`;
  добавлены ADR-0004 (role/profile separation) и ADR-0005 (review recorder).
- `.agents/decisions/` теперь предназначен только для host/project решений.
- Extraction readiness честно фиксирует оставшиеся блокеры host-binding,
  provider adapters, standalone CI и submodule invocation.

## Phase 1 review triage — 2026-06-22

- Формализованы dispositions `blocking`, `follow_up`, `accepted_risk`,
  `wont_fix` и правила планирования debt-сессий.
- Task-схема получила обязательные `Type`/`Priority`; review-derived задачи —
  `Source-*`, `Due-Before` и идемпотентный `Triage-Key`.
- Добавлены JSON Schema follow-up manifest и trusted
  `scripts/record-review-followups.sh`, создающий задачи и append-only event.
- QA read-only prompt требует русскоязычный approved review и полный
  machine-readable manifest неблокирующих findings.

## Phase 1 GitFlic control plane — 2026-06-22

- Зафиксирован проверенный API-контракт GitFlic для MR, branch/commit/blob и
  pipeline/job metadata, включая игнорирование server-side pipeline filters.
- Добавлен read-only `scripts/gitflic-ci.sh`: pagination, exact ID/SHA filter,
  jobs/job, fail-closed polling, диагностика и self-hosted runner correlation.
- Документированы границы: console stdout job через проверенные REST endpoints
  недоступен; fallback — runner service log и точное воспроизведение job image.
- CI `agentmarshal_tests` устанавливает `jq`, требуемый execution-profile launcher.

## Phase 1 execution profiles — 2026-06-22

- Добавлен отдельный источник истины `profiles/*.yaml`: роль отвечает за
  ownership/scope, execution profile — за tools/write/network/session policy.
- `qa-readonly` технически лишён write/shell: Claude запускается в safe mode
  только с `Read,Grep,Glob`; результат пишет launcher в ignored `.agents/runs/`.
- `validate.sh` проверяет profile-спеки и optional task scheduling fields
  (`Execution-Profile`, `Preferred-Vendor`, `Model-Policy`).
- Документирован recorder pattern: reviewer выдаёт аттестацию, canonical review
  сохраняет dispatcher/recorder, а не read-only агент.

## Phase 1 — 2026-06-21 (скелет + рельсы)

Добавлено:
- Каркас `agentmarshal/` (config, ADOPT, methodology, agents, adapters, scripts).
- Vendor-agnostic role-спеки: lead, frontend (active); backend, qa, release
  (reserved). Источник границ — `docs/handbook/07-team/personas.md`.
- Adapter-пайплайн: `adapters/render.sh` + Claude-адаптер → `.claude/agents/`.
  Codex/Gemini — документированные стабы.
- Рельсы: `scope-guard.sh` (diff ⊆ scope роли, без yq), `persona-status.sh`
  (health worktree), `config/settings.frontend.template.json` (суженные права),
  `config/worktree/{env.dev.example,new-agent-worktree.sh}`.
- Журнал `.agents/` (tasks/host-decisions/handoffs/reviews); framework ADR
  находятся в `agentmarshal/docs/adr/`.
- Export-скрипты сессий (`scripts/{claude_session_to_md,codex_jsonl_to_md}.py`).
- Вшивка scope-guard в pre-push hook + CI job `scope_guard` (allow_failure).

Решения: см. `docs/adr/ADR-0001` (модель команды), `ADR-0002`
(engineering-, не security-изоляция).

## Phase 1 remediation — 2026-06-21 (ревью CR-001 от Codex)

Закрыты находки ревью:
- F-001 worktree-local git identity (`git config --worktree` + extensions.worktreeConfig;
  main→lead, FE→fe; коммиты переавторизованы).
- F-002/F-003 scope-guard **fail-closed** (ref/merge-base/diff обязаны разрешаться)
  + **trusted** в CI (guard+спеки из origin/master, `--repo`/`--agents-dir`/`--strict`).
- F-004 CI scope_guard **blocking** (без allow_failure) + `merge-policy.sh`
  (task/review/reviewer≠writer) в `mr.sh merge`.
- F-005 role/journal права по `docs/adr/ADR-0003` (impl: handoffs/events; QA: reviews; Lead:
  tasks/decisions/agentmarshal); роль больше не правит свой промпт.
- F-007 безопасный worktree prep (refuse dirty/conflict).
- F-008 tracked transcript → ignored `.agents/runs/` + redaction в конвертерах.
- F-009/F-010 `validate.sh` (role-спеки + журнал) в CI; enforced/advisory разметка полей.

Отложено (с обоснованием): F-006 онбординг FE-worktree — operator-coordinated
после merge; control-plane диспетчер (GitFlic API), reviewer/CI-через-API,
full-history secret scan — относится к CR-002 (экстракция).

## Backlog (следующие фазы)
- Вынести host binding в `.agentmarshal/` и реализовать explicit project-root/config.
- Выделить provider adapters из GitFlic-specific scripts.
- Добавить standalone CI и submodule invocation fixtures.
- Рендер Codex/Gemini адаптеров (сейчас стабы).
- Активация QA → Backend → Release агентов (порядок из `docs/adr/ADR-0001`).
- Trial-benchmark прогон (2 FE + 2 BE + 1 review + 1 visual).
- Snapshot extraction в самостоятельный repository + pinned submodule cutover.
