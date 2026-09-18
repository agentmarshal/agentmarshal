Ревью CR-107 на `cc760104` закончено. Вердикт: **changes_required**, одна блокирующая находка и одна рекомендательная.

**Что сходится с контрактом:**
- **Workflow.** В repo-workflow gate теперь запускается с `--without-review`, `continue-on-error` убран, комментарий говорит «required check, not the merge authority». Остальные отличия от шаблона (uv вместо pip, ветка `master`, `uv run`, свои проверки вместо `<TEST_COMMAND>`) прокомментированы. Формулировки «advisory until Phase C» больше нигде нет.
- **Архив CR-102.** Числа совпадают с текущим кодом: `load_task_for_record` вызывается ровно в 12 местах в 6 модулях (submit_review 1, session 1, complete 3, acceptance 1, cli 4, review 2). Путей со своим отказом восемь. Что у finding review pre-run refusal есть со времён CR-101, подтверждает архивная spec CR-101 («a closed task is refused»). Перенос проверки `reopen` в guard виден в комментарии в `status.py`.
- **ADR.** Оба новых раздела помечены «non-normative». Ссылки рабочие: якорь `docs/sidecar.md#research-findings-loop` существует, `.agentmarshal/extensions/openspec.toml` тоже.
- **Тест.** Новый тест действительно закрепляет guard в sidecar-ветке `complete`. Без guard'а отказ пришёл бы из gate с другим текстом («already closed»), а тест проверяет именно «is not open (state: done)».

**Что не проверено:**
- Историю CR-102 я не видел: снапшот — не git-репозиторий. Поэтому «до» сверял только через текущий код и архив CR-101.
- Тест я не запускал: копирование в scratchpad и вызов pytest не получили разрешения. Вывод про тест выше сделан чтением кода.
- Сообщение коммита мне недоступно. Есть ли в нём grep и команды с результатами, которые требует контракт, я проверить не могу.

**Находки:**

Блокирующая: в `docs/proposals/018-session-activity-vocabulary-and-cost.md:43-44` отложенное решение про cost-поле всё ещё отсылает к неопубликованному плану («the accounting rework already in the plan»). Этой работы нет в опубликованном roadmap в `docs/overview.md`, так что это та же ситуация, что с backlog в CR-100, и второй критерий приёмки не выполнен. Похожие отсылки к неопубликованному «release plan» есть в `docs/proposals/016-…md:48` и `docs/proposals/README.md:88`.

Рекомендательная: в `.github/workflows/agentmarshal-governance.yml:37-42` комментарий gate-job'а выбросил из шаблонного текста «and nothing shipped enforces it on this provider». Это расхождение с шаблоном без комментария.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cc760104504fafc9cbf8746064e13984ef9aaef3", "verdict": "changes_required", "findings": ["CR107-docs-point-at-unpublished-plan"], "advisory_findings": ["CR107-gate-comment-drops-template-clause"]}
AGENTMARSHAL_VERDICT_END
