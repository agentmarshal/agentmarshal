---
Document-ID: agentmarshal-methodology-parallel-work
Document-Version: 3
---

# Параллельная работа: worktree-per-agent и изоляция

## Модель

Маленькая инженерная система с ролями, контрактами и авто-воротами — не «много
агентов одновременно ковыряют репозиторий». Каждой активной роли — отдельный
git worktree (`<repo>.<alias>`, ветки `<prefix>/*`), своя git identity, свои
(суженные) права. Координация — через Lead и артефакты (см. agent-comms.md).

## Уровни изоляции (от мягкого к жёсткому)

1. **sparse-checkout** — агент видит только свои папки. Удобно, но **не
   security boundary** (`git show HEAD:src/backend/...` обходит).
2. **sparse + scope-guard (pre-push/CI) + Lead review** — практичная защита от
   ошибок и дисциплина. **← наш выбор**
   ([ADR-0002](../docs/adr/ADR-0002-agent-isolation.md)).
3. **sandbox без `.git`** — реальный запрет чтения, но теряется git workflow.
4. **отдельные репозитории** — настоящие repo-level permissions, дорого
   (CI/CD, контракты, релизная координация).

Решение: **engineering isolation, не security**. Secrets обязаны находиться
вне Git tree/worktree. Жёсткие уровни (3–4) вводятся точечно для недоверенных
агентов, untrusted code или repository с чувствительными данными.

## Механика

- Создание/обновление worktree: `config/worktree/new-agent-worktree.sh <role> [slug]`
  (identity роли + dev `.env` + суженные права из шаблона).
- Перед запуском `scripts/worktree-lifecycle.sh worktree-preflight` проверяет,
  что каталог зарегистрирован через `git worktree`, использует общий Git
  common-dir и среда может записывать shared metadata. Standalone clone не
  является допустимым fallback.
- Перед задачей — ритуал открытия: `scripts/persona-status.sh <worktree>`
  (branch, behind/ahead, clean, .env, identity). Codex-урок: новая задача не
  должна стартовать с устаревшего мира (FE-standby отставал на 100+ коммитов).
- Границы держит механически `scripts/scope-guard.sh`: `git diff` ветки ⊆
  `scope_allow` роли (источник — `agents/<role>.yaml`). Вшит в pre-push + CI.
- `fe/standby`-стиль: держать standby-ветку, обновлять `git pull --ff-only
  origin master`, новую задачу — `git switch -c fe/<task> origin/master`
  (НЕ `git checkout master` внутри worktree — master занят основным worktree).

## Finalization и cleanup

Работа не считается интегрированной по наличию файлов в primary worktree.
Обязательное evidence — integration commit в Git history:

```bash
agentmarshal/scripts/worktree-lifecycle.sh finalize \
  --integration-sha <full-sha> \
  --integration-ref feat/<task> \
  --require-pushed
```

Гейт требует:

- primary `HEAD` точно равен integration SHA;
- primary worktree чист;
- integration ref указывает на тот же SHA;
- при `--require-pushed` upstream не имеет ahead/behind.

Перед удалением worker worktree:

```bash
agentmarshal/scripts/worktree-lifecycle.sh cleanup-ready \
  --worktree <path> \
  --integration-sha <full-sha> \
  --require-pushed
git worktree remove <path>
```

Запрещено копировать tracked-файлы из clone/worktree в primary как способ
интеграции. Если shared `.git` недоступен, workflow останавливается. Recovery
выполняется через bundle/fetch/cherry-pick/merge, после чего finalization
запускается повторно.

## Завершение task после merge

Worktree finalization доказывает целостность integration history, но ещё не
означает доставку в default branch. До merge task остаётся `in_review`.

После approved review exact SHA и успешного pipeline:

```bash
AGENTMARSHAL_PIPELINE_OK_SHA=<reviewed-sha> \
  agentmarshal/scripts/merge-policy.sh \
    --mr <id> --task CR-NNN --review-file .agents/runs/<review>.md
```

После фактического merge создаётся journal-only completion branch от
обновлённого target:

```bash
git fetch origin --prune
git switch -c completion/CR-NNN origin/master

agentmarshal/scripts/task-lifecycle.sh complete \
  --task CR-NNN \
  --review-task CR-NNN \
  --review-file .agents/runs/<review>.md \
  --reviewed-commit <reviewed-sha> \
  --target-ref origin/master
```

Только эта команда переносит task в `done`, канонизирует review и записывает
merge evidence. Completion branch проходит pipeline/review и сливается в
protected target через MR. Её diff ограничен journal artifacts; direct push в
target не используется. `task-lifecycle.sh audit` перепроверяет все закрытые
задачи.

## Когда параллелить

Параллельно — независимые задачи без общего sync (FE-экран + BE-фича по
готовому контракту). Последовательно — когда вторая зависит от артефакта первой
(FE ждёт API-контракт от BE). Sync point фиксируется task/event/handoff.
