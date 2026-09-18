Вердикт: **approved**, с двумя некритичными замечаниями. Все пять критериев приёмки выполнены, противоречий с ADR-0009 и ADR-0010 нет.

**Workflow.** Прогнал `diff` с `templates/github/agentmarshal-governance.yml`. В job `gate` добавлен `--without-review`, убран `continue-on-error`, есть комментарий «Required check (Variant 2), not the merge authority». Отличий от шаблона три: `uv sync --locked`, `uv run` и то, что gate берётся из checkout самого PR, а не из закреплённого релиза. Каждое помечено комментарием «Repository-specific», а для последнего прямо сказано, что оно ослабляет гарантию.

**Ссылки на невидимые записи.** Искал `backlog|register|separate RFC|release plan|not published|RFC|scheduled` по `docs/` и `openspec/changes/archive/`. Живых ссылок на неопубликованные реестры или планы не осталось. Правки ADR-0004, migration, overview и proposals 005/006/016/018/README как раз убирают такие ссылки, так что это исправления, а не косметическая правка точных документов.

**Цифры CR-102.** Нашёл 12 вызовов `load_task_for_record` в 6 модулях: `submit_review`, `complete`×3, `acceptance`, `session`, `cli`×4, `review`×2. Это совпадает с «twelve in six modules». Восемь приватных проверок и то, что проверка перед запуском ревьюера (pre-run refusal) для finding review появилась ещё в CR-101, подтверждаются ревью CR-102 в журнале («Diff удаляет восемь проверок `state != "open"`»). Сам merge diff я не видел: git-истории в snapshot нет.

**Примеры в ADR.** Якорь `../sidecar.md#research-findings-loop` существует, `.agentmarshal/extensions/openspec.toml` тоже. Оба раздела помечены «(non-normative)».

**Тест.** Запустить его не получилось: команду копирования snapshot во временную папку не одобрили. Проверил вручную. Если убрать guard в `cli.py:881`, gate пишет в stdout «already closed at base». Тест же ждёт «task CR-001 is not open (state: done)» в stderr, значит, он закрепляет именно guard. Имена `main`, `_tree_snapshot` и `_host_and_sidecar` в файле есть.

**Не проверено:** сообщение коммита мне не передали. Поэтому условия про grep и про цифры, процитированные в сообщении коммита, проверить не смог.

**Замечания (не блокируют):**

- **ADV-OVERVIEW-DIRECTION-VS-DESIGNED.** `docs/overview.md:166-169`: пункт «Contract extensions» стоит в списке под заголовком «What is designed but **not active in 0.3.0**», но сам говорит «This is a direction, not yet a design». Вдобавок имя совпадает с полем контракта `extensions` из ADR-0010, и можно подумать, что речь о нём.
- **ADV-GOVERNANCE-JOB-COMMENT-DROPPED.** `.github/workflows/agentmarshal-governance.yml:18`: в job `governance` нет комментария шаблона «Mark REQUIRED… `ci-required` attestation mode relies on», и это отличие никак не прокомментировано. Критерий приёмки говорит только о gate-jobs, поэтому это не блокер.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c42617e200f27cb96a7954e0bd4793da7bed8225", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-OVERVIEW-DIRECTION-VS-DESIGNED", "ADV-GOVERNANCE-JOB-COMMENT-DROPPED"]}
AGENTMARSHAL_VERDICT_END
