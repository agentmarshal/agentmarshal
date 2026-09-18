Всё проверил статически, запускать тесты sandbox не дал. Блокеров не нашёл.

**Что сходится с контрактом:**
- **Workflow.** Gate-job совпадает с `templates/github/agentmarshal-governance.yml`: есть `--without-review`, нет `continue-on-error`, есть комментарий «required check, not the merge authority». Отличий от шаблона три: uv-окружение вместо setup-python/pip, вызов через `uv run` и оговорка про запуск из checkout самого PR. Каждое помечено комментарием «Repository-specific». Оговорка про maintainer-run merge authority согласуется с `docs/self-hosting-workflow.md` и `docs/github-enforcement.md`.
- **Ссылки на скрытые записи.** В archived design.md adopter-small-defects больше нет отсылки к backlog. По `docs/` и `openspec/changes/archive/` я прогнал свой grep (backlog, register, release plan и т.п.). Отсылок к непубличным записям не осталось, упоминания «register» в ADR-0009 и proposal 005 относятся к register адоптера.
- **Архив CR-102.** Состояние «до» расписано так: 8 путей со своей `state != "open"`-проверкой, у `reopen` своя проверка `state != "done"`. Pre-run refusal новый только для commit review, у finding review он есть со времён CR-101. Вызовов guard'а 12 в 6 модулях. Счёт вызовов `load_task_for_record` по текущему `src/` даёт те же 12 в 6 модулях (cli 4, complete 3, review 2, submit_review, acceptance, session). Остальное совпадает с тем, что пишут review-артефакты CR-102 о содержимом merge-диффа.
- **Примеры в ADR.** Секции помечены как non-normative. Цели ссылок существуют: `docs/sidecar.md#research-findings-loop` и `.agentmarshal/extensions/openspec.toml`.
- **Тест.** Новый тест в `tests/test_placement.py` действительно пинит guard sidecar-ветки `complete` (`cli.py:881`). Без guard'а отказ пришёл бы от gate со словами «already closed at base», а строки «is not open (state: done)» в stderr не было бы. Использованные хелперы существуют, сигнатуры сходятся.

**Что проверить не смог:** commit message мне не передали. Поэтому не видно, процитированы ли там команды grep и подсчёта с результатами, как требуют критерии 2 и 3.

ADV-ADR0004-PLANNED-SCHEMA-CHANGE: в `docs/adr/ADR-0004-journal-data-model.md:139` принудительная проверка acceptance по-прежнему названа «a planned contract-schema change». Диф переписал ту же мысль в `docs/migration-v1-to-v2.md` («not been designed or scheduled yet») и в `docs/overview.md` («a direction, not yet a design»), так что документы теперь противоречат друг другу.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "2aa5800ae35e8dbd7065724eba28b5c8d6f4f0c6", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-ADR0004-PLANNED-SCHEMA-CHANGE"]}
AGENTMARSHAL_VERDICT_END
