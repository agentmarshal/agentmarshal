Изменение можно принимать. Блокирующих дефектов нет, есть одно замечание без блокировки.

Что проверил:
- **Workflow.** Сравнил `.github/workflows/agentmarshal-governance.yml` с `templates/github/agentmarshal-governance.yml`. В gate job теперь стоит `--without-review`, `continue-on-error` убран, комментарий о required check, а не merge authority, взят из шаблона дословно. Job отличается от шаблона в трёх местах: `setup-uv`/`uv sync --locked` вместо `setup-python` и `pip install`, префикс `uv run` и запуск из checkout самого PR вместо закреплённого релиза. Каждое отличие прокомментировано, и комментарий честно пишет, что из-за последнего утверждение «enforced here» слабее.
- **Ссылки на невидимые записи.** Сам прошёлся grep по `docs/` и `openspec/changes/archive/`: «backlog», «release plan», «RFC», «tracked», «planned» и похожее. В `docs/` и архиве не осталось ни одной отсылки к невидимой записи. Оставшиеся упоминания «register» (ADR-0009:23, proposal 005:14) описывают историю адоптера и не отправляют читателя к записи.
- **Цифры CR-102.** Сверил с кодом и review-артефактами CR-102 в журнале:
  - 12 вызовов `load_task_for_record` в 6 модулях: `submit_review` 1, `complete` 3, `session` 1, `acceptance` 1, `cli` 4, `review` 2.
  - Diff удалил 8 проверок `state != "open"`, как пишет ревью `01M2RZR82…`.
  - У `reopen` была своя проверка `state != "done"`.
  - Pre-run refusal для finding review существовал с CR-101: сценарий «a closed task is refused» в спеке findings-review. Для commit review он новый.
- **Примеры в ADR.** Оба раздела помечены как non-normative. Цели ссылок существуют: `docs/sidecar.md#research-findings-loop` и `.agentmarshal/extensions/openspec.toml`.
- **Тест.** Guard в sidecar-ветке `_run_complete` (`cli.py:881`) срабатывает до `run_gate`. Строка «is not open (state: done)» есть только в guard в `status.py:150` (у `brief` похожая строка, но `complete` через неё не идёт), так что тест закрепляет именно этот guard.

Что проверить не смог:
- Снапшот не git-репозиторий, поэтому commit message с цитатами grep и подсчётов по merge diff мне недоступен. Требования о цитатах в коммите остаются непроверенными.
- Новый тест я не запускал: запуск pytest не был разрешён. Проверка только статическая.

Замечание (advisory): `docs/adr/ADR-0004-journal-data-model.md:139` всё ещё называет enforcement acceptance в gate «a planned contract-schema change». Исправленный `docs/migration-v1-to-v2.md:81` теперь говорит, что изменение «has not been designed or scheduled yet», а `docs/overview.md` — что это «a direction, not yet a design». Три документа описывают одно и то же по-разному.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "2aa5800ae35e8dbd7065724eba28b5c8d6f4f0c6", "verdict": "approved", "findings": [], "advisory_findings": ["adr-0004-still-calls-acceptance-enforcement-planned"]}
AGENTMARSHAL_VERDICT_END
